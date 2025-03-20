import { useState } from "react";

export default function UploadImage({
  closeModal,
  setSearch,
  serverURL,
  setInputValue,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]); // Store file correctly
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    setLoading(true); // Show loading animation
    setUploadError(null); // Reset any previous errors

    const formData = new FormData();
    formData.append("image", selectedFile); // Append actual file

    try {
      const response = await fetch(`${serverURL}/caption`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (data.response === "okay" && data.caption.length > 0) {
        setSearch(data.caption[0]); // Set caption text
        setInputValue(data.caption[0]); // Set input value
      } else {
        setUploadError("Failed to process the image. Please try again.");
      }
    } catch (error) {
      console.error("Upload failed:", error);
      setUploadError(
        "Upload failed. Please check your connection and try again."
      );
    } finally {
      setLoading(false); // Hide loading modal
      if (!uploadError) {
        closeModal(); // Close modal after successful upload
      }
    }
  };

  return (
    <>
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center">
            <h2 className="text-xl font-bold mb-2">Processing...</h2>
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      )}

      {uploadError && (
        <div className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center">
            <h2 className="text-xl font-bold mb-2 text-red-500">Error</h2>
            <p className="text-gray-700 mb-4">{uploadError}</p>
            <button
              onClick={() => setUploadError(null)}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      <div
        className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-50"
        onClick={closeModal}
      >
        <div
          className="bg-white w-1/2 p-6 rounded-lg shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-2xl font-bold mb-4">🚀 Image ✌️ Search</h2>
          <p className="text-gray-700">
            Drag and drop your image here or click to browse
          </p>

          {/* Dropzone */}
          <div className="mt-4 border-2 border-gray-300 border-dashed rounded-lg p-8 flex justify-center items-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-10 w-10 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            <input type="file" onChange={handleFileChange} />
          </div>

          <p className="text-gray-700 mt-2">or click here to upload an image</p>

          <div className="mt-4 flex justify-end">
            <button
              onClick={handleUpload}
              className="mr-5 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              Upload
            </button>
            <button
              onClick={closeModal}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
