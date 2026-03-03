'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Check } from 'lucide-react'

interface AvatarSelectorProps {
  selectedAvatar: string
  onSelect: (avatar: string) => void
}

// Available user avatars from the /public/users folder
const userAvatars = [
  '/users/icons8-politician-female-skin-type-3-64.png',
  // Add more avatars as they are added to the folder
]

export function AvatarSelector({ selectedAvatar, onSelect }: AvatarSelectorProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-3">
          Choose Your Avatar
        </label>
        <p className="text-xs text-gray-500 mb-4">
          Select an icon to represent your profile
        </p>
      </div>

      <div className="grid grid-cols-4 sm:grid-cols-6 gap-3">
        {userAvatars.map((avatar) => (
          <button
            key={avatar}
            type="button"
            onClick={() => onSelect(avatar)}
            className={`relative aspect-square rounded-xl p-2 transition-all duration-200 ${
              selectedAvatar === avatar
                ? 'ring-2 ring-primary bg-primary/10 scale-105'
                : 'bg-white/50 hover:bg-white/80 hover:scale-105 border border-border'
            }`}
          >
            <Image
              src={avatar}
              alt="Avatar option"
              width={64}
              height={64}
              className="w-full h-full object-contain"
            />
            {selectedAvatar === avatar && (
              <div className="absolute -top-1 -right-1 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                <Check className="w-3 h-3 text-white" />
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Preview */}
      {selectedAvatar && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-br from-purple-50 to-blue-50 border border-primary/20">
          <div className="w-16 h-16 rounded-full bg-white p-2 flex items-center justify-center">
            <Image
              src={selectedAvatar}
              alt="Selected avatar"
              width={64}
              height={64}
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Selected Avatar</p>
            <p className="text-xs text-gray-500">This will appear on your profile</p>
          </div>
        </div>
      )}
    </div>
  )
}
