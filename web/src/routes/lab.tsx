import { createFileRoute } from '@tanstack/react-router'
import { LabDashboard } from '../features/lab/LabDashboard'

export const Route = createFileRoute('/lab')({ component: LabDashboard })
