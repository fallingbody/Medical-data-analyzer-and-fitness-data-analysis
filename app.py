import os
import json
from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, PROFILE_PIC_FOLDER
import threading

# Import all custom modules, including the new get_general_recommendations
from modules import database_module
from modules.ocr_module import extract_text_from_image
from modules.pdf_module import extract_text_from_pdf
from modules.nlp_module import extract_medical_parameters
from modules.fitness_module import get_recommendations, retrain_and_load_model, is_model_training, get_general_recommendations
from modules.risk_analyzer_module import analyze_risks
from modules.database_module import init_db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_PIC_FOLDER'] = PROFILE_PIC_FOLDER
app.secret_key = 'a_very_secure_and_random_secret_key_for_this_project'

# --- Automatic Retraining Logic ---
REPORT_COUNTER = 0
RETRAIN_THRESHOLD = 10 # Retrain after every 10 new reports
COUNTER_LOCK = threading.Lock()

def check_and_trigger_retraining():
    """Checks the report counter and starts a retraining job in the background."""
    global REPORT_COUNTER
    with COUNTER_LOCK:
        if REPORT_COUNTER >= RETRAIN_THRESHOLD and not is_model_training():
            print("Retraining threshold reached. Starting model retraining in the background.")
            retrain_thread = threading.Thread(target=retrain_and_load_model)
            retrain_thread.start()
            REPORT_COUNTER = 0 # Reset counter

def allowed_file(filename, extensions):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

@app.route('/')
def index():
    """Renders the main landing page."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the login process."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if database_module.check_user(username, password):
            session['username'] = username
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('analyzer'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles the user registration process."""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        name = request.form['name']
        phone = request.form['phone']

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('signup.html')

        if database_module.add_user(username, email, password, name, phone):
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists. Please choose another.', 'error')
            return render_template('signup.html')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    """Handles user profile viewing."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = database_module.get_user_by_username(session['username'])
    if user:
        user_id = user['id']
        reports = database_module.get_reports_by_user_id(user_id)
    else:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('logout'))
    
    return render_template('profile.html', user=user, reports=reports)


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Handles editing of user profile."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = database_module.get_user_by_username(session['username'])
    if not user:
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form['name']
        new_username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        
        if new_username != user['username'] and database_module.check_username_exists(new_username):
            flash('Username already taken. Please choose another one.', 'error')
            return render_template('edit_profile.html', user=user)

        if database_module.update_user_details(user['id'], name, new_username, email, phone):
            session['username'] = new_username
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Email already in use by another account.', 'error')
            return render_template('edit_profile.html', user=user)

    return render_template('edit_profile.html', user=user)


@app.route('/profile/change_photo', methods=['POST'])
def change_photo():
    """Handles changing the user's profile photo."""
    if 'username' not in session:
        return redirect(url_for('login'))
        
    user = database_module.get_user_by_username(session['username'])
    if 'photo' not in request.files:
        flash('No file part selected.', 'error')
        return redirect(url_for('profile'))
        
    file = request.files['photo']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
        filename = secure_filename(file.filename)
        unique_filename = str(user['id']) + '_' + filename
        filepath = os.path.join(app.config['PROFILE_PIC_FOLDER'], unique_filename)
        file.save(filepath)
        database_module.update_profile_photo(user['id'], unique_filename)
        flash('Profile photo updated!', 'success')
    else:
        flash('Invalid file type for photo. Please use PNG, JPG, or JPEG.', 'error')
        
    return redirect(url_for('profile'))


@app.route('/report/delete/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    """Handles the deletion of a report."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = database_module.get_user_by_username(session['username'])
    database_module.delete_report_by_id(report_id, user['id'])
    flash('Report deleted successfully.', 'info')
    return redirect(url_for('profile'))


@app.route('/report/<int:report_id>')
def view_report(report_id):
    """Displays a single, previously generated report."""
    if 'username' not in session:
        return redirect(url_for('login'))
        
    user = database_module.get_user_by_username(session['username'])
    report = database_module.get_report_by_id(report_id, user['id'])

    if not report:
        flash('Report not found or you do not have permission to view it.', 'error')
        return redirect(url_for('profile'))

    parameters = json.loads(report['parameters'])
    risks = json.loads(report['risks'])
    plans = json.loads(report['plans']) if report['plans'] else None
    
    return render_template('report_detail.html',
                           report=report,
                           parameters=parameters,
                           risks=risks,
                           plans=plans,
                           username=session['username'])


@app.route('/analyzer', methods=['GET', 'POST'])
def analyzer():
    """Handle file upload and analysis, with automatic retraining triggers."""
    global REPORT_COUNTER
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if is_model_training():
            flash('The AI model is currently updating with new data. Please try again in a moment.', 'info')
            return redirect(request.url)
            
        try:
            if 'file' not in request.files:
                flash('File part is missing. Please try again.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if not file or file.filename == '':
                flash('No file selected. Please choose a file.', 'error')
                return redirect(request.url)

            if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
                flash('Invalid file type. Only PDF, PNG, JPG, and JPEG are allowed.', 'error')
                return redirect(request.url)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if filename.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(filepath)
            else:
                extracted_text = extract_text_from_image(filepath)

            if not extracted_text or "Could not extract text" in extracted_text or len(extracted_text.strip()) < 10:
                 flash('Could not extract meaningful text from the file. It might be empty, corrupted, or unreadable.', 'error')
                 return redirect(request.url)

            parameters = extract_medical_parameters(extracted_text)
            
            personal_profile = {
                'dietary_preference': request.form.get('dietary_preference', 'Non_Veg'),
                'budget': request.form.get('budget', 'Standard'),
                'limitations': 'Yes' if request.form.getlist('limitations') else 'No',
                'activity_level': request.form.get('activity_level', 'Moderate')
            }
            health_statuses = request.form.getlist('health_status') or []

            parameters['Dietary_Preference'] = personal_profile['dietary_preference']
            parameters['Limitations'] = personal_profile['limitations']

            plans, predicted_condition = get_recommendations(parameters, health_statuses, personal_profile)
            
            if plans is None or predicted_condition is None:
                flash('Could not generate a personalized plan, but here is some general advice.', 'info')
                plans = get_general_recommendations() # This is the crucial fallback
                predicted_condition = "General Advice"

            risks = analyze_risks(parameters)

            user = database_module.get_user_by_username(session['username'])
            if user:
                report_id = database_module.save_report(
                    user['id'], filename, parameters, risks, plans, predicted_condition
                )
                
                with COUNTER_LOCK:
                    REPORT_COUNTER += 1
                check_and_trigger_retraining()
                
                return redirect(url_for('view_report', report_id=report_id))
            else:
                flash('User session error. Please log in again.', 'error')
                return redirect(url_for('login'))

        except Exception as e:
            app.logger.error(f"An unexpected error occurred in /analyzer: {str(e)}")
            flash(f'An unexpected error occurred. Please try again.', 'error')
            return redirect(request.url)

    training_status = is_model_training()
    return render_template('dashboard.html', username=session.get('username'), model_is_training=training_status)


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal Server Error: {str(error)}")
    return render_template('error.html', 
                         error_message="An internal server error has occurred. The technical team has been notified."), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)