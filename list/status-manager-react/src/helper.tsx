import { StatusType } from "./components/Status"
import { StatusChainType } from "./components/StatusChain"

export function initChains(): [StatusChainType[], StatusType[]] {
    const chains: StatusChainType[] = [
      {
        id: '1',
        name: "Draft",
        priority: 1,
        color: "green"
      },
      {
        id: '2',
        name: "Active",
        priority: 2,
        color: "pink"
      },
      {
        id: '3',
        name: "Done",
        priority: 3,
        color: "brown"
      },
      {
        id: 'id-add-chain',
        name: "",
        priority: 4,
        color: "lightgrey"
      },
    ];

    const statuses: StatusType[] = [
        {
            id: "1",
            name: "Lead obtained",
            color: "yellow",
            chain_id: "1",
            next_status_id: "2"
        },
        {
            id: "2",
            name: "Responsibility assigned",
            color: "green",
            chain_id: "1",
            next_status_id: "3"
        },
        {
            id: "3",
            name: "Meeting done",
            color: "blue",
            chain_id: "1",
            next_status_id: ""
        },
        {
            id: "4",
            name: "In Schedule",
            color: "green",
            chain_id: "2",
            next_status_id: "5"
        },
        {
            id: "5",
            name: "Issue",
            color: "red",
            chain_id: "2",
            next_status_id: ""
        },
        {
            id: "6",
            name: "Success",
            color: "green",
            chain_id: "3",
            next_status_id: ""
        },
        {
            id: "7",
            name: "Fail",
            color: "red",
            chain_id: "3",
            next_status_id: ""
        },
    ];
    return [chains, statuses];
}

