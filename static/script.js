document.addEventListener("DOMContentLoaded", function () {
        // Xử lý xóa công việc
        const deleteButtons = document.querySelectorAll(".delete-task");
    
        deleteButtons.forEach(button => {
            button.addEventListener("click", function () {
                const taskId = this.dataset.id;
    
                if (!confirm("Bạn có chắc chắn muốn xóa công việc này?")) return;
    
                fetch("/delete_task", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ task_id: taskId })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) {
                        location.reload(); // Tải lại trang sau khi xóa thành công
                    }
                })
                .catch(error => {
                    console.error("Lỗi:", error);
                    alert("Đã xảy ra lỗi khi xóa công việc.");
                });
            });
        });
    

    // Xử lý gửi công việc mới
    const taskForm = document.getElementById("taskForm");
    if (taskForm) {
        taskForm.addEventListener("submit", function (event) {
            event.preventDefault();
            let formData = new FormData(taskForm);

            fetch("/create_task", {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    taskForm.reset();
                    location.reload();
                }
            })
            .catch(error => {
                console.error("Lỗi:", error);
                alert("Đã xảy ra lỗi khi tạo công việc.");
            });
        });
    }

    // Xử lý cập nhật trạng thái công việc (hoàn thành/chưa hoàn thành)
    document.querySelectorAll(".task-status").forEach(taskCheckbox => {
        taskCheckbox.addEventListener("change", function () {
            let taskId = this.dataset.id;
            let isCompleted = this.checked;

            fetch("/update_task_status", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_id: taskId, completed: isCompleted })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
            })
            .catch(error => {
                console.error("Lỗi:", error);
                alert("Đã xảy ra lỗi khi cập nhật trạng thái công việc.");
            });
        });
    });

    // Xử lý tải lên ảnh đại diện
    const avatarForm = document.getElementById("avatarForm");
    if (avatarForm) {
        avatarForm.addEventListener("submit", function (event) {
            event.preventDefault();
            let formData = new FormData(avatarForm);

            fetch("/upload-avatar", { method: "POST", body: formData })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || "Ảnh đã được tải lên!");
                    if (data.success) {
                        location.reload();
                    }
                })
                .catch(error => {
                    console.error("Lỗi:", error);
                    alert("Đã xảy ra lỗi khi tải ảnh lên.");
                });
        });
    }
});