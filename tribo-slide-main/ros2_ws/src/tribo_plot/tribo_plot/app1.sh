#!/bin/bash

# --- CONFIGURATION ---
SESSION="tribo_ros"
WORK_DIR="~/Documents/tribo-slide/ros2_ws"
CONDA_ENV="tribo"
SETUP_CMD="source install/setup.bash"

# This is the specific path for the first 3 nodes
PY_PATH="export PYTHONPATH=/home/kang/miniconda3/envs/tribo/lib/python3.10/site-packages:\$PYTHONPATH"

# This flag file tells other terminals when 'colcon build' is done
FLAG_FILE="/tmp/tribo_build_done"

# --- 1. CLEANUP ---
# Kill the session if it already exists so we start fresh
tmux kill-session -t $SESSION 2>/dev/null

# --- 2. START SESSION (TERMINAL 1: Build + State Manager) ---
# Create session and naming it
tmux new-session -d -s $SESSION -n 'Tribo_System'

# COMMANDS FOR TERMINAL 1:
# 1. Clear old flag file
# 2. Build
# 3. Create new flag file (so others know to start)
# 4. Source setup, Export Python, Run Node
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION:0 "rm -f $FLAG_FILE" C-m
tmux send-keys -t $SESSION:0 "colcon build && touch $FLAG_FILE && $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "$PY_PATH" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo_plot state_manager" C-m

# --- 3. TERMINAL 2: Inference (Needs PYTHONPATH) ---
tmux split-window -t $SESSION
tmux select-layout -t $SESSION tiled
sleep 1 # Wait for WSL to register the new pane
tmux send-keys -t $SESSION "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION "conda activate $CONDA_ENV" C-m
# Wait for flag file
tmux send-keys -t $SESSION "while [ ! -f $FLAG_FILE ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION "$PY_PATH" C-m
tmux send-keys -t $SESSION "ros2 run tribo_plot inference" C-m

# --- 4. TERMINAL 3: App Node (Needs PYTHONPATH) ---
tmux split-window -t $SESSION
tmux select-layout -t $SESSION tiled
sleep 1
tmux send-keys -t $SESSION "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION "while [ ! -f $FLAG_FILE ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION "$PY_PATH" C-m
tmux send-keys -t $SESSION "ros2 run tribo_plot app_node" C-m

# --- 5. TERMINAL 4: SensorT (Standard) ---
tmux split-window -t $SESSION
tmux select-layout -t $SESSION tiled
sleep 1
tmux send-keys -t $SESSION "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION "while [ ! -f $FLAG_FILE ]; do sleep 1; done; $SETUP_CMD" C-m
# No Python Path here
tmux send-keys -t $SESSION "ros2 run tribo sensorT" C-m

# --- 6. TERMINAL 5: Writer V2 (Standard) ---
tmux split-window -t $SESSION
tmux select-layout -t $SESSION tiled
sleep 1
tmux send-keys -t $SESSION "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION "while [ ! -f $FLAG_FILE ]; do sleep 1; done; $SETUP_CMD" C-m
# No Python Path here
tmux send-keys -t $SESSION "ros2 run tribo writer_v2" C-m

# --- 7. FINALIZE ---
tmux select-layout -t $SESSION tiled
tmux attach-session -t $SESSION