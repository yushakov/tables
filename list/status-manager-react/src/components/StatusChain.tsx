import React, { Dispatch, SetStateAction, useState } from "react";
import { StatusType, Status } from "./Status";
import "./StatusChain.css"

export interface StatusChainType {
    id: string;
    name: string;
    priority: number;
    color: string;
}

interface StatusChainProps {
    chain: StatusChainType;
    statuses: StatusType[];
    setChainsHook: Dispatch<SetStateAction<StatusChainType[]>>;
}

export function StatusChain(props: StatusChainProps) {
    const [statuses, setStatuses] = useState(props.statuses.filter(status => status.chain_id === props.chain.id));

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault(); // Necessary to allow drop
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const statusId = e.dataTransfer.getData("statusId").replace(/status-/, "");
        const targetId = e.currentTarget.id;

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
                    newStatuses.splice(beforeIndex + 1, 0, movingStatus);
                }
            }
            return newStatuses;
        });
    };

    function rgbToHex(rgb: string) {
        const rgbArray = rgb.match(/\d+/g)!;
        return "#" + rgbArray.map(x => {
            const hex = parseInt(x).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        }).join('');
    }

    const handleChainNameDblClick = (e: React.MouseEvent) => {
        let nameInput = document.createElement('input');
        let colorInput = document.createElement('input')
        colorInput.type = "color";
        let nextSibling = e.currentTarget.nextSibling;
        const currentTarget = e.currentTarget as HTMLDivElement;
        const parent = e.currentTarget.parentNode as HTMLDivElement;
        colorInput.value = rgbToHex(getComputedStyle(parent).backgroundColor);
        console.log(colorInput.value);
        nameInput.type = "text";
        nameInput.placeholder = e.currentTarget.textContent!;
        nameInput.value = e.currentTarget.textContent!;
        nameInput.style.width = "fit-content";
        currentTarget.textContent = "";
        parent.insertBefore(nameInput, nextSibling);
        parent.insertBefore(colorInput, nameInput);
        nameInput.focus();
        nameInput.addEventListener('keypress', (event) => {
            console.log(event.key);
            if (event.key === 'Enter') {
                currentTarget.textContent = nameInput.value;
                parent.style.backgroundColor = colorInput.value;
                props.setChainsHook(chains => {
                    let newChains = chains.map(chain => {
                        if (chain.id === props.chain.id) {
                            return {...chain, name: nameInput.value, color: colorInput.value}
                        }
                        return chain;
                    });
                    return newChains;
                });
                parent.removeChild(nameInput);
                parent.removeChild(colorInput);
                console.log(colorInput.value);
            }
        });
    };

    return (
        <div className="chain"
             key={"chain-" + props.chain.id}
             id={"chain-" + props.chain.id}>
            <div style={{ backgroundColor: props.chain.color }}
                 className="chain-head"
                 id={"chain-head-" + props.chain.id}
                 onDragOver={handleDragOver}
                 onDrop={handleDrop}>
                <div
                    className="chain-name"
                    onDoubleClick={handleChainNameDblClick}>
                    {props.chain.name}
                </div>
                <div className="add-status">+</div>
            </div>
            {
                statuses.map(status => (
                    <Status
                        key={"status-" + status.id}
                        status={status}
                        onDrop={handleDrop}/>
                    ))
            }
        </div>
    );
}
