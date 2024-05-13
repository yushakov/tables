import { useState } from "react";
import "./Status.css"

export interface StatusType {
    id: string;
    name: string;
    color: string;
    chain_id: string;
    next_status_id: string;
}

interface StatusProps {
    status: StatusType;
    onDrop: (e: React.DragEvent) => void;
    clickDelete: (s: StatusType) => void;
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

    return (
        <div id={"status-" + props.status.id}
             style={{ backgroundColor: bgColor }}
             className={clsName}
             draggable="true"
             onDragOver={(e) => e.preventDefault()}
             onDrop={props.onDrop}
             onDragStart={handleDragStart}>
            <div>{props.status.name}</div>
            <div className='delete-symbol' onClick={handleClickDelete}>X</div>
            <div className='delete-dialog-container' style={{ display: showDlg }}>
                <div className='delete-dialog'>
                    <h3>Are you sure you want to delete status?</h3>
                    <p className='status-name'>{props.status.name}</p>
                    <button onClick={deleteYes}>yes</button>&nbsp;&nbsp;<button onClick={deleteCancel}>cancel</button>
                </div>
            </div>
        </div>
    );
}
