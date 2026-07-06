import logo from '../assets/abc_logo.png';
import './TopNav.css';

export default function TopNav() {
  return (
    <div className="top-nav">
      <div className="top-nav-brand">
        <img className="top-nav-logo" src={logo} alt="Company logo" />
        <span className="top-nav-divider" aria-hidden="true" />
        <span className="top-nav-wordmark">
          JAE <em>JD Creator</em>
        </span>
      </div>
      <a className="top-nav-contact" href="mailto:contact@example.com">
        Contact Us
      </a>
    </div>
  );
}
