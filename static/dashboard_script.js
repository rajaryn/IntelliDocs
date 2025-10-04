// Get references to the HTML elements we need
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const progressWrapper = document.getElementById("progress-wrapper");
const progressBar = document.getElementById("progress-bar");
const progressStatus = document.getElementById("progress-status");

// Add an event listener to the form's 'submit' event
uploadForm.addEventListener("submit", function (event) {
  // --- 1. Prevent the default page-reloading form submission ---
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file to upload.");
    return;
  }

  // --- 2. Prepare the data for sending ---
  const formData = new FormData();
  formData.append("file", file);

  // --- 3. Create a new XMLHttpRequest to handle the upload ---
  const xhr = new XMLHttpRequest();

  // --- 4. Listen for progress events ---
  xhr.upload.addEventListener("progress", function (event) {
    if (event.lengthComputable) {
      // Calculate percentage
      const percentComplete = Math.round((event.loaded / event.total) * 100);

      // Update the progress bar and status text
      progressBar.value = percentComplete;
      progressStatus.textContent = percentComplete + "%";
    }
  });

  // --- 5. Handle completion of the upload ---
  xhr.addEventListener("load", function () {
    if (xhr.status === 200 || xhr.status === 302) {
      // 302 is for Flask's redirect
      progressStatus.textContent = "Upload complete! Refreshing...";
      // Reload the page to see the new file in the list and any flashed messages
      window.location.reload();
    } else {
      progressStatus.textContent = "Upload failed. Please try again.";
      uploadBtn.disabled = false;
    }
  });

  // --- 6. Handle errors ---
  xhr.addEventListener("error", function () {
    progressStatus.textContent = "An error occurred during the upload.";
    uploadBtn.disabled = false;
  });

  // --- 7. Configure and send the request ---
  // Make the progress bar visible and disable the upload button
  progressWrapper.style.display = "block";
  uploadBtn.disabled = true;
  progressStatus.textContent = "Uploading... 0%";

  // Open a POST request to the same URL the form was pointing to
  xhr.open("POST", uploadForm.action, true);

  // Send the form data
  xhr.send(formData);
});
