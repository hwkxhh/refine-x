import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const members = [
  { name: 'Aarav Sharma', email: 'aarav@org.com', role: 'Admin', active: 'Today', status: 'Active' },
  { name: 'Priya Mehta', email: 'priya@org.com', role: 'Analyst', active: 'Yesterday', status: 'Active' },
  { name: 'Ravi Kumar', email: 'ravi@org.com', role: 'Viewer', active: '5 days ago', status: 'Active' },
]

export default function TeamPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Team</h1>
        <p className="text-sm text-text-secondary">Manage who has access to your workspaces</p>
      </div>

      <div className="dashboard-card rounded-2xl p-5">
        <div className="grid gap-3 md:grid-cols-3 mb-4">
          <input className="h-10 rounded-lg border border-input bg-card px-3 text-sm" placeholder="Email address" />
          <select defaultValue="Analyst" className="h-10 rounded-lg border border-input bg-card px-3 text-sm">
            <option>Admin</option>
            <option>Analyst</option>
            <option>Viewer</option>
          </select>
          <Button size="sm" className="h-10">Send Invite</Button>
        </div>

        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-text-secondary">
              <tr>
                <th className="text-left font-medium p-3">Name</th>
                <th className="text-left font-medium p-3">Email</th>
                <th className="text-left font-medium p-3">Role</th>
                <th className="text-left font-medium p-3">Last Active</th>
                <th className="text-left font-medium p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.email} className="border-t border-border">
                  <td className="p-3 font-medium text-foreground">{member.name}</td>
                  <td className="p-3 text-text-secondary">{member.email}</td>
                  <td className="p-3 text-text-secondary">{member.role}</td>
                  <td className="p-3 text-text-secondary">{member.active}</td>
                  <td className="p-3"><Badge variant="success">{member.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
