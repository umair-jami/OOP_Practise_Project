from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
import uuid
import streamlit as st
from dataclasses import dataclass
from typing import List, Dict

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    due_date: date
    priority: int = Field(..., ge=1, le=5)
    completed: bool = False
    
    @classmethod
    def due_date_must_not_in_past(cls, v):
        if v < date.today():
            raise ValueError('Due date must not be in the past')
        return v
    
    @classmethod
    def title_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title must not be empty or whitespace')
        return v.strip()

# Task management class to manage tasks
@dataclass
class TaskManager:
    tasks: Dict[str, Task] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = {}

    def add_task(self, task: Task):
        self.tasks[task.id] = task
        
    def update_task(self, task_id: str, updated_task: Task):
        if task_id in self.tasks:
            updated_task.id = task_id
            self.tasks[task_id] = updated_task
            return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def mark_task_complete(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id].completed = True
            return True
        return False
    
    def get_all_tasks(self) -> List[Task]:
        # Sort tasks by due date for better UX
        return sorted(self.tasks.values(), key=lambda x: x.due_date)

def main():
    st.title("Task Management App")

    # Initialize TaskManager in session state
    if "task_manager" not in st.session_state:
        st.session_state.task_manager = TaskManager()

    task_manager = st.session_state.task_manager

    # Form to add a new task
    st.subheader("Add New Task")
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description (optional)")
        due_date = st.date_input("Due Date", min_value=date.today())
        priority = st.slider("Priority", min_value=1, max_value=5, value=3)
        submit = st.form_submit_button("Add Task")

        if submit:
            try:
                task = Task(
                    title=title,
                    description=description if description else None,
                    due_date=due_date,
                    priority=priority
                )
                task_manager.add_task(task)
                st.success("Task added successfully!")
            except ValueError as e:
                st.error(f"Error: {e}")

    # Form to edit an existing task
    if "edit_task_id" in st.session_state and "edit_task" in st.session_state:
        st.subheader("Edit Task")
        edit_task = st.session_state.edit_task
        with st.form("edit_task_form", clear_on_submit=True):
            edit_title = st.text_input("Title", value=edit_task.title)
            edit_description = st.text_area("Description (optional)", value=edit_task.description or "")
            edit_due_date = st.date_input("Due Date", value=edit_task.due_date, min_value=date.today())
            edit_priority = st.slider("Priority", min_value=1, max_value=5, value=edit_task.priority)
            save = st.form_submit_button("Save Changes")

            if save:
                try:
                    updated_task = Task(
                        title=edit_title,
                        description=edit_description if edit_description else None,
                        due_date=edit_due_date,
                        priority=edit_priority,
                        completed=edit_task.completed
                    )
                    task_manager.update_task(st.session_state.edit_task_id, updated_task)
                    del st.session_state.edit_task_id
                    del st.session_state.edit_task
                    st.success("Task updated successfully!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"Error: {e}")

    # Display all tasks
    st.subheader("Tasks")
    tasks = task_manager.get_all_tasks()
    if not tasks:
        st.write("No tasks available.")
    else:
        for task in tasks:
            with st.expander(f"{task.title} (Priority: {task.priority})"):
                st.write(f"Description: {task.description or 'None'}")
                st.write(f"Due Date: {task.due_date}")
                st.write(f"Completed: {'Yes' if task.completed else 'No'}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Mark Complete", key=f"complete_{task.id}"):
                        task_manager.mark_task_complete(task.id)
                        st.rerun()
                with col2:
                    if st.button("Edit", key=f"edit_{task.id}"):
                        st.session_state.edit_task_id = task.id
                        st.session_state.edit_task = task
                        st.rerun()
                with col3:
                    if st.button("Delete", key=f"delete_{task.id}"):
                        task_manager.delete_task(task.id)
                        st.rerun()

if __name__ == "__main__":
    main()