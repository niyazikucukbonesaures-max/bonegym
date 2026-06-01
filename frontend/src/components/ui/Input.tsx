import { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { useInputInteraction } from '@/hooks/useMicroInteraction'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  interactive?: boolean
  intensity?: 'subtle' | 'medium' | 'strong'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, interactive = true, intensity = 'medium', ...props }, ref) => {
    const { inputProps } = useInputInteraction({ intensity, disabled: !interactive || props.disabled })

    return (
      <input
        ref={interactive ? inputProps.ref : ref}
        className={cn(
          'w-full rounded-lg px-3 py-2 text-[13px] text-white/90 placeholder:text-white/25',
          'bg-white/[0.05] border border-white/[0.08]',
          'focus:outline-none focus:ring-1 focus:ring-violet-500/60 focus:border-violet-500/40 focus:bg-white/[0.07]',
          'hover:border-white/[0.14] hover:bg-white/[0.06]',
          'disabled:opacity-40 disabled:cursor-not-allowed',
          'transition-all duration-150',
          className
        )}
        {...(interactive ? inputProps : {})}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
