import torch

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self, name, fmt=':f'):
        self.name = name
        self.fmt = fmt
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

    def __str__(self):
        fmtstr = '{name} {val' + self.fmt + '} ({avg' + self.fmt + '})'
        return fmtstr.format(**self.__dict__)


def accuracy(output, target, topk=(1,)):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    with torch.no_grad():
        maxk = max(topk)
        batch_size = target.size(0)

        _, pred = output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].contiguous().view(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / batch_size))
        return res


def milestones(args):
    if args.data == 'cifar100':
        if args.model == 'resnet18':
            args.__dict__['lr_MS'] = [60, 120, 160]
            args.__dict__['lr'] = [1e-1, 2*1e-2, 4*1e-3, 8*1e-4]
            args.__dict__['wr'] = [5e-4]

            if args.reg == 'SO':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 0]
                args.__dict__['wr'] = [1e-8, 1e-4, 1e-4, 1e-4, 1e-4]

            elif args.reg == 'DSO':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 0]
                args.__dict__['wr'] = [1e-8, 5*1e-4, 5*1e-4, 5*1e-4, 5*1e-4]   

            elif args.reg == 'SRIP':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [1e-3, 1e-4, 1e-5, 1e-6, 0]
                args.__dict__['wr'] = [1e-8, 1e-8, 1e-6, 1e-4, 5e-4]

            elif args.reg == 'OCNN':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [0.1]*5
                # args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 1e-8]
                args.__dict__['wr'] = [1e-4]*5
                # args.__dict__['wr'] = [1e-8, 1e-8, 1e-6, 1e-4, 5e-4]

            elif args.reg == 'ADK':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [1]*5
                # args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 1e-8]
                # args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 0]
                args.__dict__['wr'] = [5*1e-4]*5
                # args.__dict__['wr'] = [1e-8, 1e-8, 1e-6, 1e-4, 5e-4]

            elif args.reg == 'ADC':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                # args.__dict__['rr'] = [0.1]*5
                args.__dict__['rr'] = [1e-1, 1e-3, 1e-4, 1e-6, 1e-8]
                # args.__dict__['wr'] = [5*1e-4]*5
                args.__dict__['wr'] = [1e-8, 1e-8, 1e-6, 1e-4, 5e-4]

            elif args.reg == 'PH0' or args.reg == 'MST':
                args.__dict__['reg_MS'] = [20, 50, 70, 120]
                args.__dict__['rr'] = [0.1]*5
                args.__dict__['wr'] = [5*1e-4]*5            


def adjust_learning_rate(optimizer, epoch, args):
    i = 0
    j = 0
    if args.reg == 'base':
        while epoch >= args.lr_MS[i]:
            i += 1
            if i == len(args.lr_MS):
                break
        for param_group in optimizer.param_groups:
            param_group['lr'] = args.lr[i]
    else:
        while epoch >= args.lr_MS[i]:
            i += 1
            if i == len(args.lr_MS):
                break
        while epoch >= args.reg_MS[j]:
            j += 1
            if j == len(args.reg_MS):
                break
        for param_group in optimizer.param_groups:
            param_group['lr'] = args.lr[i]
            param_group['weight_decay'] = args.wr[j]
        args.r = args.rr[j]



def reg_weights(model, fc=True):
    first_conv = True
    kern_weights = []
    conv_weights = []
    for m in model.modules():
        if isinstance(m, torch.nn.Conv2d):
            if m.kernel_size[0] == 1:
                kern_weights.append(m.weight)
            else:
                if first_conv:
                    kern_weights.append(m.weight)
                    first_conv = False
                else:
                    conv_weights.append((m.weight, m.stride[0]))
        elif fc and isinstance(m, torch.nn.Linear):
            kern_weights.append(m.weight)
    return kern_weights, conv_weights



