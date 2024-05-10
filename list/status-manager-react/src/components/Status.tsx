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
}

export function Status(props: StatusProps) {
    const handleDragStart = (e: React.DragEvent) => {
        e.dataTransfer.setData("statusId", "status-" + props.status.id);
        e.dataTransfer.setData("originChainId", props.status.chain_id);
        e.dataTransfer.effectAllowed = "move";
    };

    return (
        <div id={"status-" + props.status.id}
             style={{ backgroundColor: props.status.color }}
             className="status"
             draggable="true"
             onDragOver={(e) => e.preventDefault()}
             onDrop={props.onDrop}
             onDragStart={handleDragStart}>
            {props.status.name}
        </div>
    );
}
