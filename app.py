"""
Main Flask application file for the AI Thumbnail Creator.
This file handles the web server, routing, and connects the frontend
interface with the backend image generation logic.
"""
import os
import time
from flask import Flask, render_template, request, jsonify, url_for
from main import create_thumbnail_workflow

# Initialize the Flask web application
app = Flask(__name__)

# Ensure the static output directory exists upon startup
output_folder = os.path.join('static', 'output')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

@app.route('/')
def index():
    """
    Serves the main HTML page of the application.
    """
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """
    Handles the asynchronous request from the frontend to generate a thumbnail.
    It receives a title, runs the full image generation workflow, and returns
    a JSON response with the URL to the new image or an error message.
    """
    try:
        # Get the blog title from the incoming JSON request
        data = request.get_json()
        title = data.get('title')
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        # Create a unique filename using a timestamp to prevent browser caching issues
        timestamp = int(time.time())
        output_filename = f"thumbnail_{timestamp}.png"
        output_path_for_script = os.path.join(output_folder, output_filename)
        
        # Call the main workflow function from main.py to do the heavy lifting
        create_thumbnail_workflow(title, output_path_for_script)

        # After the workflow, check if the output file was actually created
        if os.path.exists(output_path_for_script):
            # If successful, create a URL for the new image and send it back to the frontend
            image_url = url_for('static', filename=f'output/{output_filename}')
            return jsonify({'image_url': image_url})
        else:
            # If the file wasn't created, it means the backend process failed
            print("Workflow finished, but output file was not created. Sending error to frontend.")
            return jsonify({'error': 'Image generation failed. The API may be busy or an error occurred.'}), 500

    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"An error occurred in the generate route: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# This block allows the server to be started by running "python app.py"
if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save code changes
    app.run(debug=True)