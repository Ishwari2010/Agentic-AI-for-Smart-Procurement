function Header() {
  return (
    <header className="header">
      <div>
        <h1>Smart Procurement</h1>
        <p>Agent Operations & Platform</p>
      </div>

      <div className="header-right">
        <button className="notification-button">
          Notifications
        </button>

        <div className="user-profile">
          <div className="avatar">IS</div>

          <div>
            <strong>User</strong>
            <span>Administrator</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;