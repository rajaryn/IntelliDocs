from dotenv import load_dotenv
import os
load_dotenv()

from flask import Flask,session
from flask import render_template
from flask import request,redirect
from flask import flash,url_for
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask_bcrypt import Bcrypt
import database
import os
import secrets
import processing
import fitz
import ai_utils



database.init_db()  # Ensures DB and tables exist

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
bcrypt = Bcrypt(app)


# --- Cloudinary Configuration ---
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


@app.route('/')
def index():
    return render_template('signup.html')


@app.route('/signup', methods=['GET','POST'])
def register():
       if request.method=='POST': 
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # --- Basic Validation ---
        if password != confirm_password:
            error_message = "Passwords do not match."
            return render_template('signup.html', error_message=error_message, email=email)
        
        # Check if user already exists
        existing_user = database.get_user_by_email(email)
        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html', email=email)
        
        
        # Hash the password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Add user to the database
        new_user_id=database.add_user(email, password_hash)

        #Auto Login
        if new_user_id:
            session['user_id'] = new_user_id
            session['user_email'] = email
            
            flash('Account created and you are now logged in!', 'success')
            return redirect(url_for('dashboard')) # Redirect to the main page
        
        else:
            flash('An error occurred while creating your account. Please try again.', 'danger')
            return render_template('signup.html', email=email)
        

@app.route('/login', methods=['GET', 'POST'])
def login():
   
    if request.method == 'POST':
       
        email = request.form['email']
        password = request.form['password']
        user = database.get_user_by_email(email)

        if user and bcrypt.check_password_hash(user['password_hash'], password):
          
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('dashboard')) 
        else:
           
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('login')) 
        
    
    return render_template('login.html')

        
@app.route('/logout', methods=['POST'])
def logout():
   
    # Clear all data from the session dictionary
    session.clear()
    
    flash('You have been successfully logged out.', 'info')
    
    # Redirect the user to the login page
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

   
    # Fetch the documents for the currently logged-in user.
    user_id = session['user_id']
    
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    documents = database.get_documents_by_user(user_id)
    documents_for_template=[]
    for doc in documents:
        tags=doc["tags"]
        tags_list = [tag.strip() for tag in tags.split(',')]

        clean_document = {
        'id': doc["id"],
        'filename': doc["filename"],
        'url':doc["url"],
        'tags': tags_list,
        'created_at': doc["created_at"]
        }
        print(clean_document)
        documents_for_template.append(clean_document)
    
    return render_template('dashboard.html', documents=documents_for_template)

# Helper function to check for allowed file types
ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_public_id(original_filename):
    """
    Takes a filename, sanitizes it, and adds a unique suffix.
    Returns a string suitable for a Cloudinary public_id.
    """
    # 1. Get the original filename and separate its name and extension
    filename_without_ext, file_ext = os.path.splitext(original_filename)
    
    # 2. Sanitize the base filename (replace non-alphanumeric chars with '_')
    sanitized_filename = "".join(c if c.isalnum() else "_" for c in filename_without_ext)
    
    # 3. Create a unique suffix using 4 random bytes (8 hex characters)
    unique_suffix = secrets.token_hex(4)
    
    # 4. Construct and return the final, unique public_id
    return f"{sanitized_filename}_{unique_suffix}"


@app.route('/upload', methods=['POST'])
def upload_document():
    if 'user_id' not in session:
        flash('Please log in to upload files.', 'danger')
        return redirect(url_for('login'))

   
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('dashboard'))

    file = request.files['file']

    # 3. Check if the user selected a file
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('dashboard'))

    # 4. Validate the file type
    if file and allowed_file(file.filename):
        try:
           
            file_bytes=file.read()
          
            final_public_id = generate_unique_public_id(file.filename)

            # --- AI LOGIC ---
            text_content = ""
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text_content += page.get_text()
            
            tags_list = ai_utils.generate_tags_for_text(text_content)
            tags_string = ",".join(tags_list)

            summary = ai_utils.generate_summary_for_text(text_content)

            # --- Rewind the file stream back to the beginning IMP---
            file.seek(0)

            # Upload the file to Cloudinary
            # 'raw' because it's a non-image file (PDF)
            upload_result = cloudinary.uploader.upload(
                file, 
                public_id=final_public_id,
                resource_type='raw',
                )
        
            
            url = upload_result.get('secure_url')
            public_id = upload_result.get('public_id')
            user_id = session['user_id']
            
            new_doc_id=database.add_document(user_id, file.filename, url, public_id, tags_string,summary)

            if new_doc_id:
                database.update_document_status(new_doc_id, 'PROCESSING')
                processing.process_and_index_pdf(new_doc_id, file_bytes)

                flash('File uploaded successfully! Processing for search has begun.', 'success')
            else:
                flash('Failed to save file information to the database.', 'danger')

        except Exception as e:
            flash(f'An error occurred during upload: {e}', 'danger')
            
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid file type. Only PDF files are allowed.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/delete/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    
    # 1. Check if user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to delete files.', 'danger')
        return redirect(url_for('login'))
    
    # 2. Fetch the document's metadata from our database
    document_to_delete = database.get_document_by_id(doc_id)
    
    # 3. Check if the document exists
    if not document_to_delete:
        flash('Document not found or it may have already been deleted.', 'warning')
        return redirect(url_for('dashboard'))

    # 4. CRUCIAL SECURITY CHECK: Verify the logged-in user owns this document
    if document_to_delete['user_id'] != session['user_id']:
        flash('You are not authorized to delete this document.', 'danger')
        return redirect(url_for('dashboard'))
    
    print("DEBUG: Security check passed. Proceeding with deletion.")
    try:
        # 5. If all checks pass, delete the file from Cloudinary
        public_id = document_to_delete['public_id']
        cloudinary.uploader.destroy(public_id, resource_type='raw')
        
        # 6. If Cloudinary deletion is successful, delete the record from our database
        if database.delete_document_record(doc_id):
            flash('Document deleted successfully.', 'success')
        else:
            flash('File was deleted from storage, but failed to be removed from the database.', 'danger')

    except Exception as e:
        flash(f'An error occurred while deleting the file: {e}', 'danger')
    
    # 7. Finally, redirect back to the dashboard
    return redirect(url_for('dashboard'))

@app.route('/view/<int:doc_id>')
def view_document(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    document = database.get_document_by_id(doc_id)
    
    if not document or document['user_id'] != session['user_id']:
        flash('Document not found or you are not authorized to view it.', 'danger')
        return redirect(url_for('dashboard'))
    
    
   
    return render_template(
        'view_document.html', 
        document_url=document['url'], 
        document_filename=document['filename'],
        document_summary=document['summary']
    )

if __name__ == "__main__":
    app.run(debug=True)
