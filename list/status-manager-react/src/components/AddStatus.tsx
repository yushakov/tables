import "./AddStatus.css"
import { StatusType } from "./Status";

export type AddStatusProps = {
    chainName: string,
    chainId: string,
    addStatus: (status: StatusType) => void,
    newStatusId: () => string
}

function closeDialog() {
    const dialog = document.getElementById("id-add-status-dialog");
    const inputs = dialog!.getElementsByTagName('input');
    inputs.namedItem('status-name')!.value = '';
    dialog!.style.display = "none";
}


export function AddStatus(props: AddStatusProps) {
    function addStatus() {
        const dialog = document.getElementById("id-add-status-dialog");
        const inputs = dialog!.getElementsByTagName('input');
        if (inputs.namedItem('status-name')!.value.trim().length == 0) {
            inputs.namedItem('status-name')!.focus();
            return;
        }
        const newName = inputs.namedItem('status-name')!.value;
        const newColor = inputs.namedItem('status-color')!.value;
        const newStatus: StatusType = {
            id: props.newStatusId(),
            name: newName,
            color: newColor,
            chain_id: props.chainId,
            next_status_id: ""
        };
        props.addStatus(newStatus);
        closeDialog();
    }

    return (
        <div className="dialog-container" id="id-add-status-dialog">
            <div className="add-status-dialog">
                <h2>New status to:</h2>
                <h3>{props.chainName}</h3>
                <p style={{ marginBottom: "-10px" }}>Status Name:</p>
                <p><input type="text" name="status-name" width="200px;" placeholder="Status Name" /></p>
                <p>
                    Status color:&nbsp;&nbsp;
                    <input type="color" name="status-color" />
                </p>
                <p className="add-cancel-buttons">
                <input type="button" name="button-add" value="add"
                    onClick={addStatus}/>&nbsp;&nbsp;
                <input type="button" name="button-cancel" value="cancel"
                    onClick={closeDialog}/>
                </p>
            </div>
        </div>
    );
}