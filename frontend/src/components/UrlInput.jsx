import { useState } from "react";

function UrlInput({ onAnalyze, loading }) {
  const [url, setUrl] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const trimmedUrl = url.trim();

    if (!trimmedUrl) {
      return;
    }

    onAnalyze(trimmedUrl);
  };

  return (
    <div className="url-section">
      <h2>Analyze a Scholarship or Scheme</h2>

      <p className="section-description">
        Paste the official scholarship or scheme webpage URL.
        The system will automatically identify its eligibility criteria.
      </p>

      <form onSubmit={handleSubmit} className="url-form">
        <input
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com/scholarship"
          required
          disabled={loading}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Eligibility"}
        </button>
      </form>
    </div>
  );
}

export default UrlInput;