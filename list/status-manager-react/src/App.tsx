import { useState } from 'react'
import './App.css'
import { initChains } from "./helper"
import { StatusChain } from './components/StatusChain'


function App() {
  //const [chains, statuses] = initChains();
  const statuses = initChains()[1];
  const [chains, setChains] = useState(initChains()[0]);

  return (
    <>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses}
            setChainsHook={setChains}
          />
        ))}
      </div>
    </>
  )
}

export default App
