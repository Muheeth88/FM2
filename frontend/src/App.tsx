import { useMigrationStore } from './store/migrationStore'
import RepoConfiguration from './components/RepoConfiguration'
import BranchSelection from './components/BranchSelection'

function App() {
  const { step } = useMigrationStore();

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 shadow-inner">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
            QE Framework Migration Tool
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Seamlessly migrate your automation frameworks with AI-driven analysis.
          </p>
        </header>

        <main>
          {step === 1 && <RepoConfiguration />}
          {step === 2 && <BranchSelection />}
          {step === 3 && (
            <div className="text-center bg-white p-12 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold text-green-600">All Set!</h2>
              <p className="text-gray-600 mt-2">Proceeding to feature discovery and analysis...</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
