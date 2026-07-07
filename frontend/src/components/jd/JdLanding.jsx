import './JdLanding.css';

export default function JdLanding({ config, onSelectLob }) {
  const lobOptions = config?.lob_options || ['AMC', 'NBFC'];
  const labels = config?.lob_labels || {};
  const descriptions = config?.lob_descriptions || {};

  return (
    <div className="jd-landing">
      <div className="jd-landing-intro">
        <span className="jd-landing-eyebrow">Job Architecture &amp; Evaluation</span>
        <h2>Select a line of business</h2>
        <p className="jd-landing-subtitle">
          Choose where this role sits to view its job descriptions, or start a new one.
        </p>
      </div>
      <div className="jd-lob-cards">
        {lobOptions.map((lob) => (
          <div className="jd-lob-card" key={lob}>
            <span className="jd-lob-card-code">{lob}</span>
            <h3>{labels[lob] || lob}</h3>
            <p>{descriptions[lob]}</p>
            <button className="jd-lob-card-submit" onClick={() => onSelectLob(lob)}>
              Select
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
