from django.db import models
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
from .utils import custom_messages 
from .utils import load_class_indices

class PlantDiseaseClassifier:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        self.class_indices = load_class_indices()

    def predict(self, image_path):
        img = Image.open(image_path)
        img = img.resize((224, 224))  # Resize to match model input size
        img_array = np.array(img)
        img_array = img_array.astype('float32') / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        predictions = self.model.predict(img_array)
        predicted_class_index = np.argmax(predictions, axis=1)[0]

        # Assuming the model directly outputs class names
        predicted_class_name = str(predicted_class_index)  # Convert index to string

        # Use the predicted class name to retrieve the message from custom_messages
        custom_message = self.class_indices.get(predicted_class_name, "No message found")
        return custom_message
    
class ImageUpload(models.Model):
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} uploaded on {self.uploaded_at}"