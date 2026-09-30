import { useEffect, useMemo, useState } from "react";

function getApplicabilityFields(condition, fields = []) {
  if (!condition) {
    return fields;
  }

  if (Array.isArray(condition)) {
    condition.forEach((item) => getApplicabilityFields(item, fields));
    return fields;
  }

  if (typeof condition !== "object") {
    return fields;
  }

  if (condition.field) {
    fields.push(condition.field);
  }

  if (condition.all) {
    condition.all.forEach((item) => getApplicabilityFields(item, fields));
  }

  if (condition.any) {
    condition.any.forEach((item) => getApplicabilityFields(item, fields));
  }

  if (condition.not) {
    getApplicabilityFields(condition.not, fields);
  }

  return fields;
}

function criterionApplies(criterion, userData = {}) {
  if (!criterion) {
    return true;
  }

  const appliesWhen = criterion.applies_when;

  if (!appliesWhen) {
    return true;
  }

  const evaluateCondition = (condition) => {
    if (!condition) {
      return true;
    }

    if (Array.isArray(condition)) {
      return condition.every((item) => evaluateCondition(item));
    }

    if (condition.all) {
      return condition.all.every((item) => evaluateCondition(item));
    }

    if (condition.any) {
      return condition.any.some((item) => evaluateCondition(item));
    }

    if (condition.not) {
      return !evaluateCondition(condition.not);
    }

    if (!condition.field) {
      return true;
    }

    const actual = userData[condition.field];
    const expected = condition.value;
    const operator = (condition.operator || "equals").toLowerCase();

    if (actual === undefined || actual === null || actual === "") {
      return false;
    }

    if (operator === "equals") {
      return String(actual).trim().toLowerCase() === String(expected).trim().toLowerCase();
    }

    if (operator === "in") {
      const options = Array.isArray(expected) ? expected : [expected];
      return options.some(
        (item) => String(actual).trim().toLowerCase() === String(item).trim().toLowerCase()
      );
    }

    return false;
  };

  return evaluateCondition(appliesWhen);
}

function DynamicForm({ criteria, onSubmit }) {
  const [formData, setFormData] = useState({});

  const dependencyFields = useMemo(() => {
    const fields = new Set();

    (criteria || []).forEach((criterion) => {
      const condition = criterion?.applies_when;
      getApplicabilityFields(condition, []).forEach((field) => fields.add(field));
    });

    return Array.from(fields);
  }, [criteria]);

  const profileOptions = useMemo(() => {
    const options = {};

    (criteria || []).forEach((criterion) => {
      const condition = criterion?.applies_when;

      const collect = (currentCondition, fieldName) => {
        if (!currentCondition) {
          return;
        }

        if (currentCondition.field && currentCondition.field === fieldName && currentCondition.value !== undefined) {
          if (!options[fieldName]) {
            options[fieldName] = new Set();
          }

          options[fieldName].add(String(currentCondition.value));
        }

        if (currentCondition.all) {
          currentCondition.all.forEach((item) => collect(item, fieldName));
        }

        if (currentCondition.any) {
          currentCondition.any.forEach((item) => collect(item, fieldName));
        }

        if (currentCondition.not) {
          collect(currentCondition.not, fieldName);
        }
      };

      dependencyFields.forEach((fieldName) => collect(condition, fieldName));
    });

    return Object.fromEntries(
      Object.entries(options).map(([fieldName, values]) => [fieldName, Array.from(values)])
    );
  }, [criteria, dependencyFields]);

  useEffect(() => {
    const initialData = {};

    (criteria || []).forEach((criterion) => {
      initialData[criterion.id] = "";
    });

    dependencyFields.forEach((field) => {
      if (!(field in initialData)) {
        initialData[field] = "";
      }
    });

    setFormData(initialData);
  }, [criteria, dependencyFields]);

  const handleChange = (fieldName, value) => {
    setFormData((previous) => ({
      ...previous,
      [fieldName]: value,
    }));
  };

  const activeCriteria = useMemo(
    () => (criteria || []).filter((criterion) => criterionApplies(criterion, formData)),
    [criteria, formData]
  );

  const showProfileQuestions = dependencyFields.length > 0 && dependencyFields.some((field) => formData[field] === "");

  const renderInput = (criterion) => {
    const value = formData[criterion.id] ?? "";

    if (criterion.data_type === "select" || criterion.data_type === "multi_select") {
      const options = criterion.options || [];

      return (
        <select
          value={value}
          onChange={(event) => handleChange(criterion.id, event.target.value)}
          required={criterion.mandatory}
        >
          <option value="">Select an option</option>

          {options.map((option) => (
            <option value={option} key={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    if (criterion.data_type === "boolean") {
      return (
        <select
          value={value}
          onChange={(event) => handleChange(criterion.id, event.target.value)}
          required={criterion.mandatory}
        >
          <option value="">Select</option>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      );
    }

    if (criterion.data_type === "date") {
      return (
        <input
          type="date"
          value={value}
          onChange={(event) => handleChange(criterion.id, event.target.value)}
          required={criterion.mandatory}
        />
      );
    }

    if (
      criterion.data_type === "number" ||
      criterion.data_type === "percentage" ||
      criterion.data_type === "currency"
    ) {
      return (
        <input
          type="number"
          value={value}
          onChange={(event) => handleChange(criterion.id, event.target.value)}
          required={criterion.mandatory}
          min={criterion.minimum !== null ? criterion.minimum : undefined}
          max={criterion.maximum !== null ? criterion.maximum : undefined}
          step="any"
        />
      );
    }

    return (
      <input
        type="text"
        value={value}
        onChange={(event) => handleChange(criterion.id, event.target.value)}
        required={criterion.mandatory}
      />
    );
  };

  const renderProfileField = (fieldName) => {
    const value = formData[fieldName] ?? "";
    const options = profileOptions[fieldName] || [];

    if (options.length > 0) {
      return (
        <select
          value={value}
          onChange={(event) => handleChange(fieldName, event.target.value)}
          required
        >
          <option value="">Select an option</option>
          {options.map((option) => (
            <option value={option} key={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type="text"
        value={value}
        onChange={(event) => handleChange(fieldName, event.target.value)}
        required
      />
    );
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(formData);
  };

  if (!criteria || criteria.length === 0) {
    return (
      <div className="empty-form">
        <p>No structured eligibility criteria were identified.</p>
      </div>
    );
  }

  return (
    <div className="dynamic-form-section">
      <div className="section-title">
        <h2>{showProfileQuestions ? "Tell us about yourself" : "Check Your Eligibility"}</h2>
        <p>
          {showProfileQuestions
            ? "Answer a few profile questions to narrow down the rules that apply to you."
            : "Enter the information required by this scholarship or scheme."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="dynamic-form">
        {showProfileQuestions ? (
          dependencyFields
            .filter((fieldName) => formData[fieldName] === "")
            .map((fieldName) => (
              <div className="form-field" key={fieldName}>
                <label htmlFor={fieldName}>{fieldName.replace(/_/g, " ")}</label>
                {renderProfileField(fieldName)}
              </div>
            ))
        ) : (
          activeCriteria.map((criterion) => (
            <div className="form-field" key={criterion.id}>
              <label htmlFor={criterion.id}>
                {criterion.name}
                {criterion.mandatory && <span className="required">*</span>}
              </label>

              <p className="field-description">{criterion.description}</p>

              {renderInput(criterion)}
            </div>
          ))
        )}

        {!showProfileQuestions && (
          <button type="submit" className="check-button">
            Check My Eligibility
          </button>
        )}

        {showProfileQuestions && (
          <button type="submit" className="check-button">
            Continue
          </button>
        )}
      </form>
    </div>
  );
}

export default DynamicForm;