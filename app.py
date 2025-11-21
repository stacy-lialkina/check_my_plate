from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
import base64
from openai import OpenAI
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load CALORIE_DB from file
def load_calorie_db():
    """Load calorie database from CALORIE_DB file."""
    try:
        with open('CALORIE_DB', 'r', encoding='utf-8') as f:
            content = f.read()
            # Execute the file content to get CALORIE_DB dict
            local_vars = {}
            exec(content, {}, local_vars)
            return local_vars.get('CALORIE_DB', {})
    except Exception as e:
        print(f"Error loading CALORIE_DB: {e}")
        return {}

CALORIE_DB = load_calorie_db()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None
    print("Warning: OPENAI_API_KEY not set. Food recognition will not work.")

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def encode_image_to_base64(image_path):
    """Encode image to base64 string for OpenAI API."""
    try:
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def match_food_to_db(food_description, calorie_db):
    """
    Match food description from OpenAI to keys in CALORIE_DB.
    Returns the best matching key or None.
    """
    food_lower = food_description.lower()
    
    # Try exact match first
    for key in calorie_db.keys():
        if food_lower in key.lower() or key.lower() in food_lower:
            return key
    
    # Try matching by name in different languages
    for key, item in calorie_db.items():
        for lang in ['en', 'ru', 'uk']:
            name_key = f'name_{lang}'
            if name_key in item:
                item_name = item[name_key].lower()
                if food_lower in item_name or item_name in food_lower:
                    return key
    
    # Try partial matching
    food_words = food_lower.split()
    best_match = None
    best_score = 0
    
    for key, item in calorie_db.items():
        score = 0
        key_lower = key.lower()
        
        # Check if any word from description matches
        for word in food_words:
            if word in key_lower:
                score += 1
            # Check in names
            for lang in ['en', 'ru', 'uk']:
                name_key = f'name_{lang}'
                if name_key in item and word in item[name_key].lower():
                    score += 1
        
        if score > best_score:
            best_score = score
            best_match = key
    
    return best_match if best_score > 0 else None

def detect_food_items(image_path):
    """
    Detect food items in the image using OpenAI Vision API.
    
    Returns list of detected items with structure:
    [{"key": "chicken_breast_pieces", "confidence": 0.72}, ...]
    """
    if not openai_client:
        print("OpenAI client not initialized. Returning empty list.")
        return []
    
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return []
        
        # Get image format
        image = Image.open(image_path)
        image_format = image.format.lower() if image.format else 'png'
        mime_type = f'image/{image_format}'
        
        # Create prompt for OpenAI
        # Get list of available food items for better matching
        available_foods = list(CALORIE_DB.keys())[:50]  # Limit to first 50 for prompt size
        food_list = ', '.join(available_foods)
        
        prompt = f"""Analyze this food photo and identify all food items visible on the plate.

Return a JSON array with objects containing:
- "food": the name/description of the food item (in English, be specific)
- "estimated_grams": estimated portion size in grams

Focus on identifying the main food items. Be specific about the type of food (e.g., "chicken breast" not just "chicken", "cooked rice" not just "rice").

Example format:
[
  {{"food": "chicken breast", "estimated_grams": 150}},
  {{"food": "cooked rice", "estimated_grams": 200}},
  {{"food": "steamed broccoli", "estimated_grams": 100}}
]

Return ONLY valid JSON, no additional text."""

        # Call OpenAI Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4-vision-preview"
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response (in case there's extra text)
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        detected_foods = json.loads(response_text)
        
        # Match detected foods to CALORIE_DB keys
        result = []
        for item in detected_foods:
            food_name = item.get('food', '')
            if not food_name:
                continue
            
            # Try to match to database
            matched_key = match_food_to_db(food_name, CALORIE_DB)
            if matched_key:
                # Use confidence based on how well it matched
                confidence = 0.8 if matched_key else 0.5
                result.append({
                    "key": matched_key,
                    "confidence": confidence,
                    "estimated_grams": item.get('estimated_grams', 100)
                })
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response as JSON: {e}")
        print(f"Response was: {response_text if 'response_text' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []

@app.route('/')
def index():
    """Render main page with calorie database passed to template."""
    # Pass CALORIE_DB to template as JSON
    return render_template('index.html', calorie_db=json.dumps(CALORIE_DB))

@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """Analyze uploaded image and return detected food items."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Detect food items in image
        detected_items = detect_food_items(filepath)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'detected_items': detected_items
        })
    
    except Exception as e:
        # Clean up file if it exists
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
