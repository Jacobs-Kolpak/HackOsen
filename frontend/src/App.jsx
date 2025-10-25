import AppRouter from "./components/AppRouter.jsx";
import Navbar from "./components/Navbar.jsx";
import Header from "./components/Header.jsx";
import { useContext } from "react";
import { UserContext } from "./context/UserContext.jsx";
import './index.css'

const App = () => {
	const {isAuth} = useContext(UserContext)
	
	return (
		<div>
			{isAuth ? (
				<>
					<Header />
					<div className="main-content">
						<AppRouter />
					</div>
					<Navbar />
				</>
			) : (
				<AppRouter />
			)}
		</div>
	)
}

export default App