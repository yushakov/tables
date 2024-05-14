import React, { useState } from "react";
import "./Status.css"
import { rgbToHex } from "./Utils";

export interface StatusType {
    id: string;
    name: string;
    color: string;
    chain_id: string;
    next_status_id: string;
    project_count?: number;
}

interface StatusProps {
    status: StatusType;
    onDrop: (e: React.DragEvent) => void;
    clickDelete: (s: StatusType) => void;
    editStatus: (newStatus: StatusType) => void;
}

export function Status(props: StatusProps) {
    const [showDlg, setShowDlg] = useState('none');
    const [bgColor, setBgColor] = useState(props.status.color);
    const [clsName, setClassName] = useState("status");

    const handleDragStart = (e: React.DragEvent) => {
        e.dataTransfer.setData("statusId", "status-" + props.status.id);
        e.dataTransfer.setData("originChainId", props.status.chain_id);
        e.dataTransfer.effectAllowed = "move";
    };

    const handleClickDelete = () => {
        setShowDlg('block');
    }

    const deleteYes = () => {
        setShowDlg('none');
        setBgColor('red');
        setClassName('status highlight');
        setTimeout(() => {
            props.clickDelete(props.status);
        }, 1000);
    };

    const deleteCancel = () => {
        setShowDlg('none');
    };

    const handleNameDblClick = (e: React.MouseEvent) => {
        console.log(e);
        let nameInput = document.createElement('input');
        let colorInput = document.createElement('input')
        const parent1 = e.currentTarget.parentNode as HTMLDivElement;
        const parent = parent1.parentNode as HTMLDivElement;
        const currentTarget = e.currentTarget as HTMLElement;
        colorInput.type = "color";
        colorInput.value = rgbToHex(getComputedStyle(parent).backgroundColor);
        nameInput.type = "text";
        nameInput.placeholder = e.currentTarget.textContent!;
        nameInput.value = e.currentTarget.textContent!;
        nameInput.style.width = "fit-content";
        let nextSibling = e.currentTarget.nextSibling as HTMLDivElement;
        nextSibling?.appendChild(colorInput);
        nextSibling?.appendChild(nameInput);
        currentTarget.style.display = 'none';
        nextSibling!.style.display = 'block';
        nameInput.focus();
        nameInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                currentTarget.textContent = nameInput.value;
                parent.style.backgroundColor = colorInput.value;
                const newStatus: StatusType = {...props.status, name: nameInput.value, color: colorInput.value};
                props.editStatus(newStatus);
                nextSibling?.removeChild(nameInput);
                nextSibling?.removeChild(colorInput);
                currentTarget.style.display = 'block';
                nextSibling!.style.display = 'none';
            }
        });
    };

    return (
        <div id={"status-" + props.status.id}
             style={{ backgroundColor: bgColor }}
             className={clsName}
             draggable="true"
             onDragOver={(e) => e.preventDefault()}
             onDrop={props.onDrop}
             onDragStart={handleDragStart}>
            <div className="status-name-container">
                <div
                    className="status-name"
                    onDoubleClick={handleNameDblClick}>
                    {props.status.name} ({props.status.project_count})
                </div>
                <div className="status-editor"></div>
            </div>
            <div className='delete-symbol' onClick={handleClickDelete}>X</div>
            <div className='delete-dialog-container' style={{ display: showDlg }}>
                <div className='delete-dialog'>
                    <h3>Are you sure you want to delete status?</h3>
                    <p className='dialog-status-name'>{props.status.name}</p>
                    <button onClick={deleteYes}>yes</button>&nbsp;&nbsp;<button onClick={deleteCancel}>cancel</button>
                </div>
            </div>
        </div>
    );
}
