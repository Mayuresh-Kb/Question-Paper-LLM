// src/App.jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { FormProvider } from './context/FormContext';


import MainLayout from './layout/MainLayout';
import UploadPage from './components/Upload';
import ConfigurePage from './components/MarkConfig';
import DownloadPage from './components/DownLoad';
import HomePage from './pages/HomePage';
import AboutUs from './components/AboutUs';


const AppWrapper = () => {
  return (
    <FormProvider>
      <MainLayout />
    </FormProvider>
  );
};


const router = createBrowserRouter([
  {
    path: '/',
    element: <AppWrapper />,   // Wraps all pages with MainLayout + FormProvider
    children: [
      { index: true, element: <HomePage /> },         // / → home
      { path: 'upload', element: <UploadPage /> },
      { path: 'configure', element: <ConfigurePage /> },
      { path: 'download', element: <DownloadPage /> },
      { path: 'about', element: <AboutUs /> },
    ],
  },
]);


function App() {
  return <RouterProvider router={router} />;
}

export default App;