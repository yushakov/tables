import { useEffect, useRef, useState } from 'react'
import './App.css'
import { initHelperChains } from "./helper"
import { StatusChain, StatusChainType } from './components/StatusChain'
import { AddStatus } from './components/AddStatus'
import { StatusType } from './components/Status'

declare global {
  interface Window {
    dataFetchUrl: string;
    dataPushUrl: string;
    csrf: string;
  }
}

interface fetchDataType {
  chains: StatusChainType[];
  statuses: StatusType[];
}

function App() {
  const [statuses, setStatuses] = useState<StatusType[]>([]);
  const [chains, setChains] = useState<StatusChainType[]>([]);
  const statusesRef = useRef(statuses);
  const chainsRef = useRef(chains);
  const [addStatusChainName, setAddStatusChainName] = useState('');
  const [addStatusChainId, setAddStatusChainId] = useState('');

  useEffect(()=>{
    statusesRef.current = statuses;
  }, [statuses]);

  useEffect(()=>{
    chainsRef.current = chains
  }, [chains]);

  useEffect(() => {
    const fetchData= async (url: string) => {
      const response = await fetch(url);
      return response;
    };

    const getInitialStatusesAndChains = async () => {
      console.log("window fetch url:")
      console.log(window.dataFetchUrl);
      if (window.dataFetchUrl) {
        // Assuming fetchStatuses returns a Promise
        fetchData(window.dataFetchUrl)
        .then(response => response.json())
        .then((data: fetchDataType) => {
          setChains(data.chains);
          setStatuses(data.statuses);
        }).catch(error => {
          console.error("Failed to fetch statuses and chains", error);
        });
      } else {
        // Synchronously set data returned by initHelperChains
        console.log("Get data from helper.tsx")
        const [newChains, newStatuses] = initHelperChains();
        setChains(newChains);
        setStatuses(newStatuses);
      }
    };

    getInitialStatusesAndChains();
  }, []);


  function dropStatus(statusId: String, targetId: String) {
    setStatuses(prevStatuses => {
      const index = prevStatuses.findIndex(status => status.id === statusId);
      if (index === -1) return prevStatuses; // Status not found, return previous state
      const movingStatus = prevStatuses[index];
      let newStatuses = [...prevStatuses];
      if (targetId.includes("chain-head")) {
        putOnTop(newStatuses, index, movingStatus) // Add to the beginning
      }
      else {
        putInBetween(newStatuses, index, movingStatus)
      }
      return newStatuses;
    });

    function putInBetween(newStatuses: StatusType[], index: number, movingStatus: StatusType) {
      const beforeIndex = newStatuses.findIndex(status => status.id === targetId.replace(/status-/, ""))
      newStatuses.splice(index, 1)
      if (beforeIndex == newStatuses.length - 1) {
        newStatuses.push(movingStatus)
      }
      else {
        if (index > beforeIndex) {
          newStatuses.splice(beforeIndex + 1, 0, movingStatus)
        }
        else {
          newStatuses.splice(beforeIndex, 0, movingStatus)
        }
      }
    }

    function putOnTop(newStatuses: StatusType[], index: number, movingStatus: StatusType) {
      newStatuses.splice(index, 1) // Remove the item first
      newStatuses.unshift(movingStatus)
    }
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

  type DataStructure = {
    new_ids: [
      {status: {old_id: string, new_id: string}} |
      {chain: {old_id: string, new_id: string}}
    ]
  };

  function updateNewIds(data: DataStructure) {
    data.new_ids.forEach((entry) => {
      if ('status' in entry) {
        setStatuses(oldStats => {
          const newStats = oldStats.map(status => {
            if (status.id === entry.status.old_id) {
              return {...status, id: entry.status.new_id};
            }
            return status;
          });
          return newStats;
        });
      }
    });
  }

  const handleSubmit = async () => {
    fetch(window.dataPushUrl, {
      method: 'POST',
      body: new URLSearchParams([
        ['chains', JSON.stringify(chainsRef.current)],
        ['statuses', JSON.stringify(statusesRef.current)],
      ]),
      headers: {
        'X-Requested-With': 'XMLHttpRequest', // This header helps server-side to identify the request as AJAX
        'X-CSRFToken': window.csrf
      },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
      updateNewIds(data);
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
  }

  const handleStatusDelete = (status: StatusType) => {
    setStatuses(oldStatuses => {
      const newStats = [...oldStatuses];
      const index = newStats.findIndex(newStatus => newStatus.id === status.id);
      newStats.splice(index, 1);
      return newStats;
    });
  };

  return (
    <>
      <AddStatus
        newStatusId={getNewStatusId}
        chainName={addStatusChainName}
        chainId={addStatusChainId}
        addStatus={addStatus}/>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses.filter(status => status.chain_id === chain.id)}
            dropStatus={dropStatus}
            deleteStatus={handleStatusDelete}
            setChainsHook={setChains}
            setAddStatusChainName={setAddStatusChainName}
            setAddStatusChainId={setAddStatusChainId}
          />
        ))}
      </div>
      <button onClick={handleSubmit}>Submit</button>
    </>
  )
}

export default App
