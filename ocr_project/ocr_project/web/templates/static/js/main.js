document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const errorDiv = document.getElementById('error');
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');
    const uploadSection = document.getElementById('uploadSection');
    
    let progressInterval;

    function updateProgress() {
        fetch('/progress')
            .then(response => response.json())
            .then(data => {
                console.log('Progress data:', data); // Add this for debugging
                const steps = document.querySelectorAll('.step');
                steps.forEach(step => step.classList.remove('active', 'completed'));
    
                // Find current step and update status
                const currentStepElement = document.querySelector(`[data-step="${data.step}"]`);
                if (currentStepElement) {
                    currentStepElement.classList.add('active');
                    const detailsElement = currentStepElement.querySelector('.step-details');
                    if (detailsElement) {
                        detailsElement.textContent = data.details;
                    }
    
                    // Mark previous steps as completed
                    let prevElement = currentStepElement.previousElementSibling;
                    while (prevElement) {
                        prevElement.classList.add('completed');
                        prevElement = prevElement.previousElementSibling;
                    }
                }
    
                // Check if processing is complete
                if (data.step === 'complete' || data.status === 'complete') { // Check both conditions
                    console.log('Processing complete, clearing interval'); // Debug log
                    clearInterval(progressInterval);
                    // Wait a moment before showing results
                    setTimeout(() => {
                        progressSection.style.display = 'none';
                        resultSection.style.display = 'block';
                    }, 1000);
                } else if (data.status === 'error') {
                    clearInterval(progressInterval);
                    errorDiv.textContent = data.details;
                    progressSection.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error fetching progress:', error);
                clearInterval(progressInterval);
                errorDiv.textContent = 'Error checking progress';
                progressSection.style.display = 'none';
            });
    }

    function updateDashboard(data) {
        // Parse the JSON string if it's a string
        const formData = typeof data === 'string' ? JSON.parse(data) : data;

        // Personal Information
        document.getElementById('lastName').textContent = getFieldValue(formData, 'section2', 'שם משפחה');
        document.getElementById('firstName').textContent = getFieldValue(formData, 'section2', 'שם פרטי');
        document.getElementById('idNumber').textContent = getFieldValue(formData, 'section2', 'ת.ז');
        
        // Set gender based on checkbox values
        const genderFields = getSubFields(formData, 'section2', 'מין');
        if (genderFields) {
            const gender = genderFields.find(f => f.value === true);
            document.getElementById('gender').textContent = gender ? gender.label : '';
        }

        // Contact Information
        document.getElementById('phone').textContent = getFieldValue(formData, 'section2', 'טלפון קווי');
        document.getElementById('mobile').textContent = getFieldValue(formData, 'section2', 'טלפון נייד');
        
        // Construct and set address
        const street = getFieldValue(formData, 'section2', 'רחוב');
        const houseNum = getFieldValue(formData, 'section2', 'מס\' בית');
        const entrance = getFieldValue(formData, 'section2', 'כניסה');
        const apartment = getFieldValue(formData, 'section2', 'דירה');
        const city = getFieldValue(formData, 'section2', 'יישוב');
        const postalCode = getFieldValue(formData, 'section2', 'מיקוד');
        
        const fullAddress = `${street} ${houseNum}, ${entrance ? 'Entrance ' + entrance + ',' : ''} ${apartment ? 'Apt ' + apartment + ',' : ''} ${city} ${postalCode}`.trim();
        document.getElementById('address').textContent = fullAddress;

        // Injury Details
        document.getElementById('injuryDate').textContent = getFieldValue(formData, 'section3', 'בתאריך');
        document.getElementById('injuryTime').textContent = getFieldValue(formData, 'section3', 'בשעה');
        document.getElementById('accidentLocation').textContent = getFieldValue(formData, 'section3', 'כאשר עבדתי ב');
        document.getElementById('injuredBodyPart').textContent = getFieldValue(formData, 'section3', 'האיבר שנפגע');
        
        // Medical Information
        const healthFundFields = getSubFields(formData, 'section5', 'קופת חולים');
        if (healthFundFields) {
            const healthFund = healthFundFields.find(f => f.value === true);
            document.getElementById('healthFund').textContent = healthFund ? healthFund.label : '';
        }
        
        // Get accident nature from location type
        const accidentLocationFields = getSubFields(formData, 'section3', 'מקום התאונה');
        if (accidentLocationFields) {
            const accidentType = accidentLocationFields.find(f => f.value === true);
            document.getElementById('accidentNature').textContent = accidentType ? accidentType.label : '';
        }
        
        // Medical diagnoses
        const diagnoses = [
            getFieldValue(formData, 'section5', 'אבחנה רפואית 1'),
            getFieldValue(formData, 'section5', 'אבחנה רפואית 2')
        ].filter(Boolean).join(', ');
        document.getElementById('diagnoses').textContent = diagnoses;

        // Accident Description
        document.getElementById('accidentDescription').textContent = getFieldValue(formData, 'section3', 'נסיבות הפגיעה / תיאור התאונה');
        document.getElementById('accidentAddress').textContent = getFieldValue(formData, 'section3', 'כתובת מקום התאונה');
    }

    // Helper function to get field value
    function getFieldValue(data, section, label) {
        const sectionData = data[section];
        if (sectionData && sectionData.fields) {
            const field = sectionData.fields.find(f => f.label === label);
            return field ? field.value : '';
        }
        return '';
    }

    // Helper function to get sub-fields
    function getSubFields(data, section, label) {
        const sectionData = data[section];
        if (sectionData && sectionData.fields) {
            const field = sectionData.fields.find(f => f.label === label);
            return field ? field.sub_fields : null;
        }
        return null;
    }

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        const fileInput = document.getElementById('pdfFile');
        
        if (!fileInput.files.length) {
            errorDiv.textContent = 'Please select a file';
            return;
        }
    
        errorDiv.textContent = '';
        uploadSection.style.display = 'none';
        progressSection.style.display = 'block';
        resultSection.style.display = 'none'; // Ensure result section is hidden
        
        // Start progress checking
        progressInterval = setInterval(updateProgress, 1000);
    
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            console.log('Process completed, updating dashboard with:', data); // Debug log
            clearInterval(progressInterval); // Clear the interval
            progressSection.style.display = 'none'; // Hide progress
            resultSection.style.display = 'block'; // Show results
            updateDashboard(data); // Update the dashboard with the data
        })
        .catch(error => {
            console.error('Error:', error);
            errorDiv.textContent = error.message || 'Error processing file';
            uploadSection.style.display = 'block';
            progressSection.style.display = 'none';
            resultSection.style.display = 'none';
            clearInterval(progressInterval);
        });
    });

    // File input change handler for better UX
    document.getElementById('pdfFile').addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name || 'Choose PDF file';
        document.querySelector('.file-label').textContent = fileName;
    });
});