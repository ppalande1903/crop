from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from PIL import Image
from .models import PlantDiseaseClassifier, ImageUpload
from .forms import ImageUploadForm
from .utils import custom_messages
from huggingface_hub import InferenceClient
import io


# Initialize Hugging Face Inference Client
HF_TOKEN = "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"



# Function to call Hugging Face API
def get_disease_description(disease_name):
    client = InferenceClient(
    "google/gemma-2-2b-it",
    token=HF_TOKEN,
    )
    prompt = (
        f"Provide detailed information about the plant disease called '{disease_name}'. "
        "Focus on the causes, symptoms. "
        "Generate a paragraph of 4-5 lines specifically about this disease."
        f"Stick strictly to '{disease_name}'."
        "Do not ask for follow up question from user."
    )
    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        stream=False,  # Changed to False to get the complete response
    )
    return response.choices[0].message['content']

def classify_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.cleaned_data['image']

            # Save uploaded image
            image_instance = ImageUpload.objects.create(image=uploaded_image)

            # Load classifier and make prediction
            classifier = PlantDiseaseClassifier('classifier/plant_disease_prediction_model.h5')
            prediction = classifier.predict(uploaded_image)  # Assuming PIL Image object for prediction
            
            # Get the corresponding message from custom_messages
            custom_message = custom_messages.get(prediction, "No message found")
           

            # Get detailed description from Hugging Face API
            detailed_insight = get_disease_description(prediction)
            request.session['detailed_insight'] = detailed_insight
            

            return render(request, 'classifier/classify.html', {
                'message': custom_message,
                'detailed_insight': detailed_insight,
                'form': form,
                'uploaded_image': image_instance,
                
            })
        
    else:
        form = ImageUploadForm()

    return render(request, 'classifier/classify.html', {'form': form})
