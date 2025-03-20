import { useState, useEffect, useRef, lazy, Suspense } from "react";
import Navbar from "./components/Navbar";

const serverURL = "http://10.32.12.27:8000";
const bentomlURL = "http://10.32.7.223:3000";

// Lazy load the Video component
const LazyVideo = lazy(() => import("./components/LazyVideo"));

function App() {
  const [search, setSearch] = useState("");
  const [typeButton, setTypeButton] = useState("image");
  const [strictSearch, setStrictSearch] = useState(false);
  const [selectedServered, setSelectedServered] = useState("SERVER 1: FASTAPI");
  const [media, setMedia] = useState([]);
  const videoCache = useRef(new Map());

  useEffect(() => {
    const fetchMedia = async () => {
      var searchWord = search;
      if (search && strictSearch) {
        // if strict search is enabled, then say for example "hot dog" is the searched then split
        // it by space and make the input as "hot AND dog" so that it will search for both hot and dog
        const words = search.split(" ");
        searchWord = words.join(" AND ");
      }

      const baseURL =
        selectedServered === "SERVER 1: FASTAPI" ? serverURL : bentomlURL;

      try {
        const response = await fetch(baseURL + "/query", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: searchWord || "*",
            type: typeButton,
            n: 100,
          }),
        });
        const data = await response.json();
        if (data.response === "okay") {
          setMedia(data.results);
        }
      } catch (error) {
        console.error("Error fetching media:", error);
      }
    };

    fetchMedia();
  }, [search, typeButton, strictSearch, selectedServered]);

  return (
    <div>
      <Navbar
        search={search}
        setSearch={setSearch}
        typeButton={typeButton}
        setTypeButton={setTypeButton}
        setSelectedServered={setSelectedServered}
        strictSearch={strictSearch}
        setStrictSearch={setStrictSearch}
        serverURL={serverURL}
      />
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {media.map((item, index) => (
            <div key={index} className="grid gap-4">
              {item.type === "image" ? (
                <div>
                  <img
                    className="h-auto max-w-full rounded-lg"
                    src={serverURL + `/images/${item.filename}`}
                    alt={item.caption}
                  />
                  <p className="text-center text-sm text-gray-700 mt-2">
                    {item.caption}
                  </p>
                </div>
              ) : (
                <Suspense
                  fallback={<div className="h-40 bg-gray-200 rounded-lg" />}
                >
                  <LazyVideo
                    serverURL={serverURL}
                    filename={item.filename}
                    timestamp={item.timestamp}
                    videoCache={videoCache}
                    caption={item.caption}
                  />
                </Suspense>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
