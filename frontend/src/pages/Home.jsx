import { useState } from "react";

import UrlInput from "../components/UrlInput";
import CriteriaCard from "../components/CriteriaCard";
import DynamicForm from "../components/DynamicForm";
import EligibilityResult from "../components/EligibilityResult";
import LoadingState from "../components/LoadingState";

import {
  analyzeScholarshipUrl,
  checkEligibility,
} from "../services/api";


function Home() {
  const [loading, setLoading] = useState(false);

  const [analysis, setAnalysis] = useState(null);

  const [error, setError] = useState("");

  const [eligibilityResult, setEligibilityResult] =
    useState(null);


  const handleAnalyze = async (url) => {

    setLoading(true);
    setError("");
    setAnalysis(null);
    setEligibilityResult(null);

    try {

      const data =
        await analyzeScholarshipUrl(url);

      setAnalysis(data);

    } catch (err) {

      console.error(err);

      const message =
        err?.response?.data?.detail ||
        "Unable to analyze this webpage.";

      setError(message);

    } finally {

      setLoading(false);

    }
  };


 const handleFormSubmit = async (
  userData
) => {

  setError("");

  setEligibilityResult(null);


  try {

    const data =
      await checkEligibility(
        criteria,
        userData
      );


    if (!data.success) {

      throw new Error(
        "Eligibility evaluation failed."
      );

    }


    setEligibilityResult(
      data.result
    );


  } catch (err) {

    console.error(err);

    const message =
      err?.response?.data?.detail ||
      err?.message ||
      "Unable to evaluate eligibility.";

    setError(message);

  }

};


  const eligibility =
    analysis?.eligibility;

  const criteria =
    eligibility?.criteria || [];


  return (
    <main className="home">

      <section className="hero">

        <div className="hero-badge">
          AI Eligibility Analyzer
        </div>

        <h1>
          Understand Any Scholarship
          <br />
          Before You Apply
        </h1>

        <p>
          Paste a scholarship or public-benefit
          webpage and let AI identify the
          eligibility requirements automatically.
        </p>

      </section>


      <UrlInput
        onAnalyze={handleAnalyze}
        loading={loading}
      />


      {loading && (
        <LoadingState />
      )}


      {error && (
        <div className="error-message">
          <strong>
            Unable to analyze this URL
          </strong>

          <p>{error}</p>
        </div>
      )}


      {analysis && eligibility && (
        <>

          {/* =================================================
              SCHEME INFORMATION
          ================================================= */}

          <section className="scheme-section">

            <h2>
              {eligibility.scheme_name}
            </h2>

            {eligibility.provider && (
              <p>
                Provider:{" "}
                <strong>
                  {eligibility.provider}
                </strong>
              </p>
            )}

            <p>
              {eligibility.summary}
            </p>

            <div className="source-url">
              Source:{" "}
              <a
                href={analysis.source.url}
                target="_blank"
                rel="noreferrer"
              >
                {analysis.source.url}
              </a>
            </div>

          </section>


          {/* =================================================
              CRITERIA
          ================================================= */}

          <section className="criteria-section">

            <div className="section-title">

              <h2>
                Eligibility Criteria
              </h2>

              <p>
                These requirements were extracted
                from the source webpage.
              </p>

            </div>


            <div className="criteria-grid">

              {criteria.map(
                (criterion) => (
                  <CriteriaCard
                    criterion={criterion}
                    key={criterion.id}
                  />
                )
              )}

            </div>

          </section>


          {/* =================================================
              DOCUMENTS
          ================================================= */}

          {eligibility.required_documents &&
            eligibility.required_documents.length >
              0 && (

              <section className="documents-section">

                <h2>
                  Required Documents
                </h2>

                <ul>

                  {eligibility.required_documents.map(
                    (document, index) => {
                      // Handle both old string format and new object format
                      const docName = typeof document === 'string' 
                        ? document 
                        : document.name;
                      const docDescription = typeof document === 'object' 
                        ? document.description 
                        : null;
                      const docMandatory = typeof document === 'object' 
                        ? document.mandatory 
                        : true;
                      const applicableWhen = typeof document === 'object'
                        ? document.applies_when
                        : null;
                      
                      return (
                        <li key={index}>
                          <strong>{docName}</strong>
                          {!docMandatory && <span className="optional-badge">Optional</span>}
                          {docDescription && <p>{docDescription}</p>}
                          {applicableWhen && (
                            <p className="applicability-note">
                              Applies to: <em>{JSON.stringify(applicableWhen.value || 'specific applicants')}</em>
                            </p>
                          )}
                        </li>
                      );
                    }
                  )}

                </ul>

              </section>
            )}


          {/* =================================================
              DYNAMIC FORM
          ================================================= */}

          <DynamicForm
            criteria={criteria}
            onSubmit={handleFormSubmit}
          />


          {/* =================================================
              RESULT
          ================================================= */}

          <EligibilityResult
            result={eligibilityResult}
          />

        </>
      )}

    </main>
  );
}

export default Home;