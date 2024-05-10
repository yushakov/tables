// import { useState } from 'react'
import './App.css'
import { initChains } from "./helper"
import { StatusChain } from './components/StatusChain'


function App() {
  const [chains, statuses] = initChains();

  return (
    <>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses}
          />
        ))}
      </div>
    </>
  )
}

export default App
