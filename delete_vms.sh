for vm_id in $(qm list | awk 'NR>1 {print $1}'); do
    echo "Deleting VM $vm_id..."
    qm stop $vm_id 2>/dev/null
    qm destroy $vm_id --purge
    echo "VM $vm_id deleted."
done
