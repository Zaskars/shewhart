import dash_bootstrap_components as dbc


def Navbar():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Manage Bindings", href="/manage_bindings")),
        ],
        brand="Shewhart cards",
        brand_href="/",
        color="white",
        dark=False,
    )
    return navbar
