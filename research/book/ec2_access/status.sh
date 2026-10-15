cd /opt/minimax || { echo "no /opt/minimax"; exit 0; }
echo "== $(date -u '+%F %T') UTC | $(hostname)"
sudo -u ec2-user bash deploy/status.sh 2>&1 | head -16
echo "== git"
sudo -u ec2-user git log --oneline -1
sudo -u ec2-user git status --short --untracked-files=no | head -5
echo "== end"
