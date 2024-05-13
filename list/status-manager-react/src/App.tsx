import { SyntheticEvent, useEffect, useRef, useState } from 'react'
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
  const [pageState, setPageState] = useState('saved');

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
        if (pageState === 'modified') {
            const message = 'You have unsaved changes. Are you sure you want to leave?';
            event.returnValue = message; // Standard for most browsers
            return message; // For some older browsers
        }
        return undefined;
    };

    // Set up the event listener
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Clean up the event listener
    return () => {
        window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [pageState]);

  useEffect(()=>{
    statusesRef.current = statuses;
    chainsRef.current = chains;
  }, [statuses, chains]);

  // useEffect(()=>{
  //   chainsRef.current = chains;
  // }, [statuses, chains]);

  useEffect(() => {
    const fetchData= async (url: string) => {
      const response = await fetch(url);
      return response;
    };

    const getInitialStatusesAndChains = async () => {
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
      setPageState('saved');
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

    if (pageState === 'saved') {
      setPageState('modified');
    }

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
    if (pageState === 'saved') {
      setPageState('modified');
    }
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
    console.log(data.new_ids)
    data.new_ids.filter(entry => 'status' in entry).forEach((entry) => {
      if ('status' in entry) {
        setStatuses(oldStats => {
          const newStats = oldStats.map(status => {
            if (status.id === entry.status.old_id) {
              console.log("Update status from " + status.id + " to " + entry.status.new_id);
              return {...status, id: entry.status.new_id};
            }
            return status;
          });
          return newStats;
        });
      }
    });

    data.new_ids.filter(entry => 'chain' in entry).forEach((entry) => {
      if ('chain' in entry) {
        setChains(oldChains => {
          const newChains = oldChains.map(chain => {
            if (chain.id === entry.chain.old_id) {
              console.log("Update chain from " + chain.id + " to " + entry.chain.new_id);
              return {...chain, id: entry.chain.new_id};
            }
            return chain;
          });
          return newChains;
        });
        setStatuses(oldStats => {
          const newStats = oldStats.map(status => {
            if (status.chain_id === entry.chain.old_id) {
              return {...status, chain_id: entry.chain.new_id};
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
      setPageState('saved');
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
    if (pageState === 'saved') {
      setPageState('modified');
    }
  };

  function getNewChainId() {
    const newChains = chains.filter(chain => chain.id.includes("new"));
    if (newChains.length > 0) {
      return "new-" + String(Number(newChains.sort((a, b) => {
        return Number(a.id.replace("new-", "")) - Number(b.id.replace("new-", ""))
      })[newChains.length - 1].id.replace("new-", "")) + 1);
    }
    return "new-1";
  }

  const handleAddChain = (e: SyntheticEvent) => {
    e.preventDefault();
    setChains(existing => {
      const newChain: StatusChainType = {
        id: getNewChainId(),
        name: "new chain",
        color: "lightblue",
        priority: chains.reduce((max, chain) => chain.priority > max ? chain.priority : max, chains[0].priority) + 1
      };
      const newChains = [...existing, newChain];
      return newChains;
    });
    if (pageState === 'saved') {
      setPageState('modified');
    }
  };

  const editStatus = (newStatus: StatusType) => {
    setStatuses(oldStats => {
      const newStats = oldStats.map(status => {
        if (status.id === newStatus.id) {
          return newStatus;
        }
        return status;
      });
      return newStats;
    });
    setPageState('modified');
  };

  return (
    <>
      <AddStatus
        newStatusId={getNewStatusId}
        chainName={addStatusChainName}
        chainId={addStatusChainId}
        addStatus={addStatus}/>
      <button
        onClick={handleSubmit}
        disabled={ pageState === 'saved' ? true : false }
        style={{ marginLeft: "20px"}}>
          Submit
      </button>
      <a href='#' onClick={handleAddChain} style={{ marginLeft: "20px"}}>Add Chain</a>
      <div style={{ display: "flex", padding: "20px"}}>
        {chains.map(chain => (
          <StatusChain
            key={chain.id}
            chain={chain}
            statuses={statuses.filter(status => status.chain_id === chain.id)}
            editStatus={editStatus}
            dropStatus={dropStatus}
            deleteStatus={handleStatusDelete}
            setChainsHook={setChains}
            setModified={() => setPageState('modified')}
            setAddStatusChainName={setAddStatusChainName}
            setAddStatusChainId={setAddStatusChainId}
          />
        ))}
      </div>
    </>
  )
}

export default App
