from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuring file upload settings
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
POSTS_FILE = 'posts.json'  # File to store blog posts

# Function to read posts from the file
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return []  # Return an empty list if the file doesn't exist

# Function to save posts to the file
def save_posts(posts):
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f)

# In-memory storage for blog posts (loaded from the file)
blog_posts = load_posts()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        # Ensure category is not empty or 'undefined'
        if not category or category.lower() == 'undefined':
            category = 'Uncategorized'  # Default category if not provided or if 'undefined'
        
        date = datetime.now().strftime('%Y-%m-%d')

        # File upload logic
        if 'image' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = f'/{file_path}'

            # Add new blog post
            blog_post = {
                'id': len(blog_posts) + 1,
                'title': title,
                'content': content,
                'category': category,
                'date': date,
                'image': image_url
            }
            blog_posts.append(blog_post)
            save_posts(blog_posts)  # Save posts to the file
            return jsonify({"message": "Post added successfully!"}), 200
        else:
            return jsonify({"error": "Invalid file format!"}), 400

    # GET request to fetch posts (with optional category filtering)
    category_filter = request.args.get('category')  # Get the category filter from query params
    if category_filter:
        # Filter posts by the category
        filtered_posts = [post for post in blog_posts if post.get('category') == category_filter]  # Using .get() to avoid KeyError
        return jsonify(filtered_posts)  # Return the filtered posts
    
    # If no category is specified, return all posts
    return jsonify(blog_posts)

@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global blog_posts
    # Filter out the post by its ID
    blog_posts = [post for post in blog_posts if post['id'] != post_id]
    save_posts(blog_posts)  # Save the updated posts to the file
    return jsonify({"message": "Post deleted successfully!"}), 200

@app.route('/cleanup', methods=['GET'])
def cleanup_posts():
    global blog_posts
    # Remove any posts with 'undefined' category
    blog_posts = [post for post in blog_posts if post.get('category') != 'undefined']
    save_posts(blog_posts)  # Save the cleaned list of posts back to the file
    return jsonify({"message": "Posts with 'undefined' category have been removed."}), 200

@app.route('/reset', methods=['GET'])
def reset_posts():
    global blog_posts
    # Clear all posts in memory and on disk
    blog_posts = []
    save_posts(blog_posts)  # Save an empty list to the file
    return jsonify({"message": "All posts have been deleted. You can start fresh!"}), 200

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
