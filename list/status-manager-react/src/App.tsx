import { useState } from 'react'
import './App.css'
import { initChains } from "./helper"
import { StatusChain } from './components/StatusChain'
import { AddStatus } from './components/AddStatus'
import { StatusType } from './components/Status'


function App() {
  const [statuses, setStatuses] = useState(initChains()[1]);
  const [statusesOfAddStatus, setStatusesOfAddStatus] = useState(initChains()[1]);
  const [chains, setChains] = useState(initChains()[0]);
  const [addStatusChainName, setAddStatusChainName] = useState('');
  const [addStatusChainId, setAddStatusChainId] = useState('');

  function dropStatus(statusId: String, targetId: String) {
    setStatuses(prevStatuses => {
      const index = prevStatuses.findIndex(status => status.id === statusId);
      if (index === -1) return prevStatuses; // Status not found, return previous state
      const movingStatus = prevStatuses[index];
      let newStatuses = [...prevStatuses];
      if (targetId.includes("chain-head")) {
        newStatuses.splice(index, 1); // Remove the item first
        newStatuses.unshift(movingStatus); // Add to the beginning
      }
      else {
        const beforeIndex = prevStatuses.findIndex(status => status.id === targetId.replace(/status-/, ""));
        newStatuses.splice(index, 1);
        if (beforeIndex == prevStatuses.length - 1) {
            newStatuses.push(movingStatus);
        }
        else {
          if (index > beforeIndex) {
            newStatuses.splice(beforeIndex + 1, 0, movingStatus);
          }
          else {
            newStatuses.splice(beforeIndex, 0, movingStatus);
          }
        }
      }
      return newStatuses;
    });
  }

  function addStatus(status: StatusType) {
    setStatuses([...statuses, status]);
  }

  function getNewStatusId() {
    const newStatuses = statuses.filter(status => status.id.includes("new"));
    if (newStatuses.length > 0) {
      return "new-" + String(Number(newStatuses.sort((a, b) => {
        return Number(a.id.replace("new-", "")) - Number(b.id.replace("new-", ""))
      })[newStatuses.length - 1].id.replace("new-", "")) + 1);
    }
    return "new-1";
  }

  return (
    <>
      <AddStatus
        newStatusId={getNewStatusId}
        chainName={addStatusChainName}
        chainId={addStatusChainId}
        statusSet={statusesOfAddStatus}
        addStatus={addStatus}/>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses.filter(status => status.chain_id === chain.id)}
            dropStatus={dropStatus}
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
