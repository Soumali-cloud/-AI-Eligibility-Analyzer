function CriteriaCard({ criterion }) {
  const getRequirementText = () => {
    if (
      criterion.minimum !== null &&
      criterion.minimum !== undefined &&
      criterion.maximum !== null &&
      criterion.maximum !== undefined
    ) {
      return `${criterion.minimum} – ${criterion.maximum}`;
    }

    if (
      criterion.minimum !== null &&
      criterion.minimum !== undefined
    ) {
      return `≥ ${criterion.minimum}`;
    }

    if (
      criterion.maximum !== null &&
      criterion.maximum !== undefined
    ) {
      return `≤ ${criterion.maximum}`;
    }

    if (criterion.options && criterion.options.length > 0) {
      return criterion.options.join(", ");
    }

    if (criterion.value) {
      return criterion.value;
    }

    return "See description";
  };

  return (
    <div className="criteria-card">
      <div className="criteria-header">
        <h3>{criterion.name}</h3>

        {criterion.mandatory && (
          <span className="mandatory-badge">
            Mandatory
          </span>
        )}
      </div>

      <p className="criteria-description">
        {criterion.description}
      </p>

      <div className="criteria-details">
        <div>
          <strong>Requirement</strong>
          <span>{getRequirementText()}</span>
        </div>

        <div>
          <strong>Type</strong>
          <span>{criterion.data_type}</span>
        </div>

        <div>
          <strong>Category</strong>
          <span>{criterion.category}</span>
        </div>
      </div>

      {criterion.conditional && (
        <div className="conditional-box">
          <strong>Conditional requirement</strong>
          <p>
            {criterion.condition_description ||
              "This requirement applies only under certain conditions."}
          </p>
        </div>
      )}

      <details className="source-details">
        <summary>View source evidence</summary>

        <p>
          {criterion.source_text}
        </p>
      </details>
    </div>
  );
}

export default CriteriaCard;