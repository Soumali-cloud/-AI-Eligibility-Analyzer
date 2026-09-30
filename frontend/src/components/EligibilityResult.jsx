function EligibilityResult({ result }) {
  if (!result) {
    return null;
  }

  const isEligible = result.eligible === true;
  const isNotEligible = result.eligible === false;

  return (
    <section className="result-section">

      <div
        className={`result-card ${
          isEligible
            ? "eligible"
            : isNotEligible
            ? "not-eligible"
            : "unknown"
        }`}
      >
        <div className="result-icon">
          {isEligible
            ? "✓"
            : isNotEligible
            ? "✕"
            : "?"}
        </div>

        <div>
          <h2>
            {isEligible
              ? "You appear to be eligible"
              : isNotEligible
              ? "You are not eligible"
              : "Eligibility could not be determined"}
          </h2>

          <p>
            {result.message ||
              "Eligibility analysis completed."}
          </p>
        </div>
      </div>

      {result.results &&
        result.results.length > 0 && (
          <div className="criterion-results">

            <h3>
              Criterion-by-Criterion Analysis
            </h3>

            {result.results.map(
              (item, index) => (
                <div
                  className="criterion-result"
                  key={index}
                >
                  <div>
                    <strong>
                      {item.criterion?.name ||
                        "Criterion"}
                    </strong>

                    <p>
                      {item.reason ||
                        item.message ||
                        "No explanation available."}
                    </p>
                  </div>

                  <span
                    className={`status ${
                      item.status
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              )
            )}
          </div>
        )}
    </section>
  );
}

export default EligibilityResult;