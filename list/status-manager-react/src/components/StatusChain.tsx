import React, { Dispatch, SetStateAction } from "react";
import { StatusType, Status } from "./Status";
import "./StatusChain.css"

export interface StatusChainType {
    id: string;
    name: string;
    priority: number;
    color: string;
}

interface StatusChainProps {
    chain: StatusChainType,
    statuses: StatusType[],
    dropStatus: (statusId: String, targetId: String) => void,
    deleteStatus: (s: StatusType) => void,
    setChainsHook: Dispatch<SetStateAction<StatusChainType[]>>,
    setAddStatusChainName: Dispatch<SetStateAction<string>>,
    setAddStatusChainId: Dispatch<SetStateAction<string>>,
    setModified: () => void;
}

export function StatusChain(props: StatusChainProps) {
    const statuses = props.statuses;

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault(); // Necessary to allow drop
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const statusId = e.dataTransfer.getData("statusId").replace(/status-/, "");
        const targetId = e.currentTarget.id;
        props.dropStatus(statusId, targetId);
    };

    function rgbToHex(rgb: string) {
        const rgbArray = rgb.match(/\d+/g)!;
        return "#" + rgbArray.map(x => {
            const hex = parseInt(x).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        }).join('');
    }

    const handleAddStatusClick = () => {
        const dialog = document.getElementById("id-add-status-dialog")!;
        dialog.style.display = "block";
        const inputs = dialog.getElementsByTagName('input');
        inputs.namedItem('status-name')!.focus();
        props.setAddStatusChainName(props.chain.name);
        props.setAddStatusChainId(props.chain.id);
        return;
    };

    const handleChainNameDblClick = (e: React.MouseEvent) => {
        let nameInput = document.createElement('input');
        let colorInput = document.createElement('input')
        colorInput.type = "color";
        let nextSibling = e.currentTarget.nextSibling;
        const currentTarget = e.currentTarget as HTMLDivElement;
        const parent = e.currentTarget.parentNode as HTMLDivElement;
        colorInput.value = rgbToHex(getComputedStyle(parent).backgroundColor);
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
                props.setModified();
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
                <div className="add-status"
                     onClick={handleAddStatusClick}>+</div>
            </div>
            {
                statuses.map(status => (
                    <Status
                        key={"status-" + status.id}
                        status={status}
                        clickDelete={props.deleteStatus}
                        onDrop={handleDrop}/>
                    ))
            }
        </div>
    );
}
