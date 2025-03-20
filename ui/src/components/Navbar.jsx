import { useState, useEffect, useRef } from "react";
import UploadImage from "./UploadImage";

export default function Navbar({
  search,
  setSearch,
  typeButton,
  setTypeButton,
  setSelectedServered,
  strictSearch,
  setStrictSearch,
  serverURL,
}) {
  const [showModal, setShowModal] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState("SERVER 1: FASTAPI");
  const [inputValue, setInputValue] = useState(search);
  const timeoutRef = useRef(null);

  // Clear timeout on component unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    timeoutRef.current = setTimeout(() => {
      setSearch(value);
    }, 400); // 2 second delay
  };

  const closeModal = () => setShowModal(false);

  const handleServerSelect = (server) => {
    setSelectedServer(server);
    setSelectedServered(server);
    setDropdownOpen(false);
  };

  return (
    <div className="flex justify-between items-center p-4 bg-white shadow-md">
      <h1
        className={
          "flex-1 text-4xl font-bold text-blue-500 bg-clip-text text-transparent bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 animate-gradient" +
          //change gradient color with time
          (new Date().getSeconds() % 2 === 0
            ? " bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
            : " bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500")
        }
      >
        🔥 Semantic UI
      </h1>

      {/* BUTTONS */}
      <div className="flex flex-2 space-x-4 text-lg translate-x-10">
        <button
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-gray-300 ${
            typeButton === "image" ? "bg-gray-300" : "bg-gray-200"
          }`}
          onClick={() => setTypeButton("image")}
        >
          🖼 Images
        </button>
        <button
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-gray-300 ${
            typeButton === "videos" ? "bg-gray-300" : "bg-gray-200"
          }`}
          onClick={() => setTypeButton("video")}
        >
          📹 Videos
        </button>
      </div>

      {/* SEARCH BAR WITH DROPDOWN */}
      <div className="relative w-full max-w-lg flex">
        {/* CHECKBOX */}
        <div className="flex flex-row items-center space-x-2">
          <label>
            <input
              type="checkbox"
              checked={strictSearch}
              onChange={(e) => setStrictSearch(e.target.checked)}
            />
          </label>
          <span>👩‍💻 Advance</span>
        </div>
        <input
          type="text"
          placeholder="Search..."
          className="w-full border-2 border-gray-300 p-3 pr-20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={inputValue}
          onChange={handleInputChange}
        />
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
          <button
            className="bg-orange-200 text-black px-4 py-2 rounded-lg hover:bg-blue-700"
            onClick={() => setDropdownOpen(!dropdownOpen)}
          >
            {selectedServer} ▼
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg">
              <div
                className="px-4 py-2 hover:bg-gray-200 cursor-pointer"
                onClick={() => handleServerSelect("SERVER 1: FASTAPI")}
              >
                SERVER 1: FASTAPI
              </div>
              <div
                className="px-4 py-2 hover:bg-gray-200 cursor-pointer"
                onClick={() => handleServerSelect("SERVER 2: BENTOML")}
              >
                SERVER 2: BENTOML
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SOMETHING NEW BUTTON */}
      <div className="ml-4">
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 text-white bg-gradient-to-r from-purple-500 to-pink-500 rounded-full shadow-lg hover:opacity-90 transition"
        >
          🚀 Something New
        </button>
      </div>

      {/* MODAL */}
      {showModal && (
        <UploadImage
          closeModal={closeModal}
          setSearch={setSearch}
          serverURL={serverURL}
          setInputValue={setInputValue}
        />
      )}
    </div>
  );
}
