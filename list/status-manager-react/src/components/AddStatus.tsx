import { Dispatch, SetStateAction } from "react";
import "./AddStatus.css"
import { StatusChainType } from "./StatusChain";
import { StatusType } from "./Status";

export type AddStatusProps = {
    chainName: string,
    chainId: string,
    statusSet: StatusType[],
    setStatuses: Dispatch<SetStateAction<StatusType[]>>,
    onChange?: (chainName: string) => void;
    setChainsHook: Dispatch<SetStateAction<StatusChainType[]>>;
}

function closeDialog() {
    const dialog = document.getElementById("id-add-status-dialog");
    const inputs = dialog!.getElementsByTagName('input');
    inputs.namedItem('status-name')!.value = '';
    dialog!.style.display = "none";
}


export function AddStatus(props: AddStatusProps) {
    //console.log(props);

    function addStatus() {
        const dialog = document.getElementById("id-add-status-dialog");
        const inputs = dialog!.getElementsByTagName('input');
        if (inputs.namedItem('status-name')!.value.trim().length == 0) {
            inputs.namedItem('status-name')!.focus();
            return;
        }
        const newName = inputs.namedItem('status-name')!.value;
        const newColor = inputs.namedItem('status-color')!.value;
        console.log(props.chainName);
        console.log(props.chainId);
        props.setStatuses(prevStatuses => {
            let newStatuses = [...prevStatuses];
            const newStatus: StatusType = {
                id: "-1",
                name: newName,
                color: newColor,
                chain_id: props.chainId,
                next_status_id: ""
            };
            console.log(newName);
            newStatuses.push(newStatus);
            return newStatuses;
        })
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
                    <input type="color" name="status-color" value="#000000" />
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