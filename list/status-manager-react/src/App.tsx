import { useState } from 'react'
import './App.css'
import { initChains } from "./helper"
import { StatusChain } from './components/StatusChain'
import { AddStatus } from './components/AddStatus'


function App() {
  const statuses = initChains()[1];
  const [statusesOfAddStatus, setStatusesOfAddStatus] = useState(initChains()[1]);
  const [chains, setChains] = useState(initChains()[0]);
  const [addStatusChainName, setAddStatusChainName] = useState('');
  const [addStatusChainId, setAddStatusChainId] = useState('');

  return (
    <>
      <AddStatus
        setChainsHook={setChains}
        chainName={addStatusChainName}
        chainId={addStatusChainId}
        statusSet={statusesOfAddStatus}
        setStatuses={setStatusesOfAddStatus}/>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses}
            setChainsHook={setChains}
            setStatusesOfAddStatus={setStatusesOfAddStatus}
            setAddStatusChainName={setAddStatusChainName}
            setAddStatusChainId={setAddStatusChainId}
          />
        ))}
      </div>
    </>
  )
}

export default App
