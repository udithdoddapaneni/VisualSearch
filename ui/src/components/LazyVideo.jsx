import { useEffect, useState, useRef } from "react";

const LazyVideo = ({ serverURL, filename, timestamp, videoCache, caption }) => {
  const videoRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const observer = useRef(null);

  // Cache the video URL for the base file without timestamps
  const baseVideoURL = serverURL + `/videos/${filename}`;
  const cachedVideoURL = videoCache.current.get(filename) || baseVideoURL;

  useEffect(() => {
    observer.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsLoaded(true);
            observer.current.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );

    if (videoRef.current) {
      observer.current.observe(videoRef.current);
    }

    return () => observer.current && observer.current.disconnect();
  }, []);

  useEffect(() => {
    if (!videoCache.current.has(filename)) {
      videoCache.current.set(filename, baseVideoURL);
    }
  }, [filename, videoCache]);

  return (
    <div ref={videoRef} className="relative">
      {isLoaded ? (
        <video
          className="h-auto max-w-full rounded-lg"
          src={cachedVideoURL + `#t=${timestamp}`}
          poster={cachedVideoURL + `#t=${timestamp}`}
          muted
          loop
          onMouseOver={(e) => e.target.play()}
          onMouseOut={(e) => e.target.pause()}
        />
      ) : (
        <div className="h-40 bg-gray-200 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      )}
      <p className="text-center text-sm text-gray-700 mt-2">{caption}</p>
    </div>
  );
};

export default LazyVideo;
