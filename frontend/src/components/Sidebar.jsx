import { NavLink } from "react-router-dom";

function Sidebar() {
  const menuItems = [
    { name: "Dashboard", path: "/" },
    { name: "Document Intelligence", path: "/documents" },
    
    { name: "Requests", path: "/requests" },
    { name: "Contracts", path: "/contracts" },
    { name: "Inventory", path: "/inventory" },
    { name: "Emails", path: "/emails" },
    { name: "Operations", path: "/operations" },
    { name: "Logs", path: "/logs" },
    { name: "Users", path: "/users" },
  ];

  return (
    <aside className="sidebar">

      

      <div>
          <h2>Smart Procurement</h2>
          <span>Agentic Operations</span>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              isActive
                ? "nav-item active"
                : "nav-item"
            }
          >
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span>Agent Platform</span>
        <small>v1.0</small>
      </div>

    </aside>
  );
}

export default Sidebar;