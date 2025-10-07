"""
Frontend Integration Guide for Cloudinary Image Uploads

This file contains example JavaScript code for integrating with the Cloudinary image upload API.
Use this as a reference for your React frontend.
"""

# Example JavaScript/React code for uploading images:

"""
// Utility function for uploading images to Cloudinary via your Django API
const uploadImageToCloudinary = async (imageFile, folder = 'uploads') => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('folder', folder);

  try {
    const response = await fetch('/api/food/upload/image/', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header, let browser set it for FormData
    });

    const result = await response.json();
    
    if (response.ok) {
      return {
        success: true,
        imageData: result.image
      };
    } else {
      return {
        success: false,
        error: result.error
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Example React component for image upload
const ImageUploader = ({ onImageUploaded, folder = 'food_images' }) => {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Upload to Cloudinary
    setUploading(true);
    const result = await uploadImageToCloudinary(file, folder);
    setUploading(false);

    if (result.success) {
      onImageUploaded(result.imageData);
    } else {
      alert(`Upload failed: ${result.error}`);
    }
  };

  return (
    <div className="image-uploader">
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        disabled={uploading}
      />
      
      {uploading && <p>Uploading...</p>}
      
      {preview && (
        <img 
          src={preview} 
          alt="Preview" 
          style={{ maxWidth: '200px', maxHeight: '200px' }}
        />
      )}
    </div>
  );
};

// Example usage in a food item form
const FoodItemForm = () => {
  const [foodData, setFoodData] = useState({
    name: '',
    price: '',
    image: null
  });

  const handleImageUploaded = (imageData) => {
    setFoodData(prev => ({
      ...prev,
      image: imageData.url  // Use the Cloudinary URL
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Submit food item with Cloudinary image URL
    const response = await fetch('/api/food/meals/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify(foodData)
    });
    
    // Handle response...
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Food name"
        value={foodData.name}
        onChange={(e) => setFoodData(prev => ({...prev, name: e.target.value}))}
      />
      
      <input
        type="number"
        placeholder="Price"
        value={foodData.price}
        onChange={(e) => setFoodData(prev => ({...prev, price: e.target.value}))}
      />
      
      <ImageUploader onImageUploaded={handleImageUploaded} folder="food_images" />
      
      {foodData.image && <img src={foodData.image} alt="Food preview" />}
      
      <button type="submit">Create Food Item</button>
    </form>
  );
};

// For user profile pictures
const ProfilePictureUploader = ({ currentImageUrl, onImageUpdated }) => {
  const handleImageUploaded = async (imageData) => {
    // Update user profile with new Cloudinary URL
    const response = await fetch('/api/auth/profile/edit/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        profile_picture: imageData.url
      })
    });
    
    if (response.ok) {
      onImageUpdated(imageData.url);
    }
  };

  return (
    <div>
      {currentImageUrl && (
        <img src={currentImageUrl} alt="Current profile" className="current-avatar" />
      )}
      
      <ImageUploader onImageUploaded={handleImageUploaded} folder="profile_pictures" />
    </div>
  );
};

export { uploadImageToCloudinary, ImageUploader, FoodItemForm, ProfilePictureUploader };
"""