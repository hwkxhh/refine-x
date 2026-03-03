'use client'

import { useState } from 'react'
import { User, Bell, Shield, Palette, Database, CreditCard, Save } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
        <p className="text-text-secondary">Manage your account and preferences</p>
      </div>

      {saved && (
        <Alert variant="success">Settings saved successfully!</Alert>
      )}

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Profile Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-accent-coral flex items-center justify-center text-white text-2xl font-bold">
              JD
            </div>
            <div>
              <Button variant="outline" size="sm">Change Avatar</Button>
              <p className="text-xs text-text-muted mt-2">JPG, PNG or GIF (max. 2MB)</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <Input label="First Name" defaultValue="John" />
            <Input label="Last Name" defaultValue="Doe" />
          </div>

          <Input label="Email Address" type="email" defaultValue="john@example.com" />
          
          <Input label="Company" defaultValue="Acme Inc." />
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { label: 'Email notifications', description: 'Receive email updates about your projects' },
            { label: 'Analysis complete', description: 'Get notified when data analysis is finished' },
            { label: 'Weekly reports', description: 'Receive weekly summary of your activity' },
            { label: 'Product updates', description: 'Get notified about new features and updates' }
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between py-3 border-b border-border last:border-0">
              <div>
                <p className="font-medium text-foreground">{item.label}</p>
                <p className="text-sm text-text-secondary">{item.description}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked={index < 2} className="sr-only peer" />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium text-foreground mb-4">Password</h4>
            <div className="space-y-3">
              <Input label="Current Password" type="password" />
              <Input label="New Password" type="password" />
              <Input label="Confirm New Password" type="password" />
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <h4 className="font-medium text-foreground mb-3">Two-Factor Authentication</h4>
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-secondary">Add an extra layer of security to your account</p>
              <Button variant="outline" size="sm">Enable 2FA</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium text-foreground mb-3">Theme</h4>
            <div className="grid grid-cols-3 gap-4">
              {['Light', 'Dark', 'Auto'].map((theme) => (
                <button
                  key={theme}
                  className="p-4 rounded-lg border border-border hover:border-primary transition-colors text-center"
                >
                  <div className="w-12 h-12 rounded-lg bg-muted mx-auto mb-2"></div>
                  <span className="text-sm font-medium text-foreground">{theme}</span>
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Data Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-border">
            <div>
              <p className="font-medium text-foreground">Data retention</p>
              <p className="text-sm text-text-secondary">Keep project data for 90 days after deletion</p>
            </div>
            <select defaultValue="90 days" className="h-9 px-3 rounded-lg border border-input bg-card text-sm">
              <option>30 days</option>
              <option>90 days</option>
              <option>1 year</option>
              <option>Forever</option>
            </select>
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <p className="font-medium text-foreground">Auto-save</p>
              <p className="text-sm text-text-secondary">Automatically save changes as you work</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-4">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSave}>
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>

      {/* Danger Zone */}
      <Card className="border-error/20">
        <CardHeader>
          <CardTitle className="text-error">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">Delete Account</p>
              <p className="text-sm text-text-secondary">Permanently delete your account and all data</p>
            </div>
            <Button variant="danger" size="sm">Delete Account</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
